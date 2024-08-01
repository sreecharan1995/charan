## coding: utf-8

import json
import re
# import os
# import subprocess
import time
from re import Match
# from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from kubernetes.client.models.v1_env_from_source import \
    V1EnvFromSource  # type: ignore
from kubernetes.client.models.v1_env_var import V1EnvVar  # type: ignore
from kubernetes.client.models.v1_volume import V1Volume  # type: ignore
from kubernetes.client.models.v1_volume_mount import \
    V1VolumeMount  # type: ignore

from common.auth.auth_manager import APIKEY_PREFIX
from common.domain.augmented_event import AugmentedEvent
from common.domain.event_sources import EB_EVENT_SOURCE_SCHEDULER
from common.domain.k8.job import Job
from common.domain.k8.pod import Pod
from common.logger import log
from common.service.aws.eb import Eb
from common.service.aws.k8 import K8
from common.service.configs_remote_service import ConfigsRemoteService
from common.service.deps_remote_service import DepsRemoteService
from common.service.permissions_service import PermissionService
# from common.service.permissions_service import PermissionService
from common.utils import Utils
from scheduler.domain.event_tool_config import EventToolConfig
from scheduler.domain.job_request import JobRequest
from scheduler.scheduler_settings import SchedulerSettings
from scheduler.service.aws.scheduler_ddb import SchedulerDdb
from scheduler.service.custom_json_encoder import CustomJsonEncoder


class SchedulerService:
    """Methods to handle scheduled jobs.
    
    Contains methods to schedule script executions, create an retrieve job requests, spawn k8 jobs,
    lookup remote configs based on event data, update job requests and generate progress events, among others.
    """

    _configs_remote_service: ConfigsRemoteService
    _deps_remote_service: DepsRemoteService
    _eb: Eb

    def __init__(self, settings: SchedulerSettings):

        self._settings = settings
        self._configs_remote_service = ConfigsRemoteService(settings=settings)
        self._scheduler_ddb: SchedulerDdb = SchedulerDdb(settings=settings)
        self._deps_remote_service: DepsRemoteService = DepsRemoteService(settings=settings)
        self._k8_service: K8 = K8()      
        self._eb = Eb(settings)

    def lookup_config(self, event_type: str, event_path: str,
                      event_person: str) -> Optional[EventToolConfig]:

        config_name: str = f"{self._settings.ESCH_EVENT_TOOLS_CONFIG_NAME}"  # maybe use as sufix in the future

        log.debug(
            f"[CONFIGS] looking up config for name '{config_name} at path '{event_path}' as user '{event_person}'"
        )

        # TODO: TBI: use token to impersonate event person
        event_person_token: str = f"{APIKEY_PREFIX}{self._settings.MS_CONFIGS_APIKEY}" if len(self._settings.MS_CONFIGS_APIKEY.strip()) > 0 else PermissionService.retrieve_token_for_person(event_person)
    
        json_config: Optional[Dict[
            str, Any]] = self._configs_remote_service.get_config(
                config_name, path=event_path, token=event_person_token) 

        if json_config is None:
            log.warning(
                f"[CONFIGS] no config was found for name '{config_name}' at path '{event_path}' as user '{event_person}'"
            )
            return None

        event_tools_map: Optional[Dict[str, Any]] = json_config.get(
            "configuration", dict()).get("event_types", None)

        if event_tools_map is None:
            log.warning(
                f"[CONFIGS] remote service answer with unusable config data: {str(json_config)}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Temporary error using a remote service")

        event_tools_map_lc: Dict[str, Any] = {
            k.lower(): v
            for k, v in event_tools_map.items()
        }  # dict with lower case keys

        event_json = event_tools_map_lc.get(event_type.lower(),
                                            None)  # lookup in lower case

        if event_json is None:
            log.warning(
                f"[CONFIGS] no effective config matching event type '{event_type}' was found for name '{config_name}' at path '{event_path}' as user '{event_person}'"
            )
            return None

        event_config: Optional[EventToolConfig] = EventToolConfig.from_dict(
            event_json)

        if event_config is None or len(event_config.tool_to_run.strip()) == 0:
            log.warning(
                f"[CONFIGS] invalid or incomplete tool config matching event type '{event_type}' for name '{config_name}' at path '{event_path}' as user '{event_person}'"
            )
            return None

        return event_config

    def register(self,
                 augmented_event: AugmentedEvent,
                 triggering_event_type: str,
                 event_tool_config: EventToolConfig,
                 schedule_after_seconds: Optional[int] = 0) -> bool:

        job_id: str = augmented_event.normalized_job_id()

        log.info(
            f"(JOB:{job_id}) registering job request for execution. tool '{event_tool_config.tool_to_run}'. schedule in {schedule_after_seconds} seconds"
        )

        now_ns: int = time.time_ns()
        due_ns: Optional[int] = now_ns + schedule_after_seconds * pow(
            10, 9) if schedule_after_seconds is not None else None

        job_request: Optional[
            JobRequest] = self._scheduler_ddb.get_job_request(job_id)

        if job_request is not None:
            log.warning(f"(JOB:{job_id}) already registered")
            return False

        job_request: Optional[
            JobRequest] = self._scheduler_ddb.new_job_request(
                job_id=job_id,
                due_ns=due_ns,
                triggering_event_type=triggering_event_type,
                tool_config_json=event_tool_config.__dict__,
                event_json=augmented_event.event)

        return job_request is not None

    def reset_job_request(self, job_id: str) -> bool:

        reset: Optional[bool] = self._scheduler_ddb.update_job_as_unprepared(job_id) 

        if reset is None:
            log.warning(f"(JOB:{job_id}) unsable to reset job request as unprepared")            
            return False

        return reset

    def create_k8_job(self, job_id: str) -> bool:

        job_name: str = self._job_container_name_from_job_id(job_id)

        try:
            job: Optional[Job] = self._k8_service.get_job(job_name=job_name,
                                                          raise_errors=True)
        except BaseException as be:
            log.warning(
                f"(JOB:{job_id}) container '{job_name}': unable to check if already exists. {be}"
            )
            return False

        if job is not None:
            log.warning(
                f"(JOB:{job_id}) container '{job_name}': already exist. job status is '{job.get_status()}'"
            )
            return False
        
        hostname: Optional[str] = Utils.get_hostname()

        if hostname is None:
            log.warning(
                f"(JOB:{job_id}) container '{job_name}': unable to detect current hostname"
            )                    
            matching_pods: List[Pod] = list( filter(lambda p: p.name.startswith("scheduler-service-exec"), self._k8_service.list_pods() or []))
            pod: Optional[Pod] = matching_pods[0] if len(matching_pods) >= 1 else None
            if pod is None:
                log.warning(
                    f"(JOB:{job_id}) container '{job_name}': unable to detect hostname from list of pods"
                )
                return False
            else:
                log.debug(f"(JOB:{job_id}) using pod {pod.name} as reference for configuration")
        else:            
            pod: Optional[Pod] = self._k8_service.get_pod(
                pod_name=hostname)  # hostname is the pod name        

            if pod is None:
                log.warning(
                    f"(JOB:{job_id}) container '{job_name}': unable to retrieve pod data"
                )
                return False

        # current_image: Optional[str] = pod.get_image_name()  # use first container

        # if current_image is None:
        #     log.warning(
        #         f"(JOB:{job_id}) container '{job_name}': unable to extract image name to use, from pod data"
        #     )
        #     return False
        tapi_image: str = self._settings.ESCH_TAPI_IMAGE_TAG
        
        env_from: List[V1EnvFromSource] = pod.get_env_from_list() or [] # use first container

        vols: List[V1Volume] = pod.volumes

        vol_mounts: List[V1VolumeMount] = pod.get_vol_mounts_list() or [] # use first container

        filtered_vol_mounts: List[V1VolumeMount] = list(filter(lambda m: not m.mount_path.startswith('/var/'), vol_mounts)) # type: ignore

        env_list: List[V1EnvVar] = []

        job_file: str = self._job_confdata_file(job_id)

        env_list.append(V1EnvVar(name="JOBCONF_JOB_ID", value=f"{job_id}"))
        env_list.append(V1EnvVar(name="JOBCONF_JOB_NAME", value=f"{job_name}"))
        env_list.append(V1EnvVar(name="JOBCONF_JOB_FILE", value=f"{job_file}"))

        job: Optional[Job] = self._k8_service.create_job(
            job_name=job_name,
            app_name="scheduler-service-exec",
            image=tapi_image,
            command=[
                "/root/runjob"
            ],
            env_from=env_from,                        
            vols=vols,
            env_list=env_list,
            vol_mounts=filtered_vol_mounts,
            backoff_limit=self._settings.ESCH_JOB_BACKOFF_LIMIT,
            ttl_seconds=60 * 60 * self._settings.ESCH_JOB_PODS_TTL_HOURS)

        if job is not None:
            log.info(f"(JOB:{job_id}) container '{job_name}': created")
            return True

        log.warning(
            f"(JOB:{job_id}) container '{job_name}': failed to be created")

        return False

    def _job_confdata_file(self, job_id: str) -> str:
        return f"{self._settings.ESCH_JOBCONF_BASEDIR}/{job_id}.json"

    def store_job_confdata(self, job_id: str, event_dict: Dict[str,Any], tool_config: Dict[str,Any], profile_packages: List[str]) -> bool:

        data_dict: Dict[str,Any] = {
            "event": event_dict,
            "tool_config": tool_config,
            "profile_packages": profile_packages
        }

        filename: str = self._job_confdata_file(job_id)

        log.debug(f"(JOB:{job_id}) confdata: storing on '{filename}'")        

        try:                        
            with open(filename, 'w') as outfile:
                json.dump(data_dict, outfile, cls=CustomJsonEncoder)                
        except BaseException as be:
            log.error(f"(JOB:{job_id}) confdata: failed to store on shared fs. {be}")
            return False

        return True

    def retrieve_job_confdata(self, job_id: str) -> Optional[Tuple[Dict[str,Any], Dict[str,Any], Dict[str,Any]]]:

        filename: str = self._job_confdata_file(job_id)

        log.debug(f"(JOB:{job_id}) confdata: storing on '{filename}'")        

        try:
            with open(filename, 'r') as inputfile:
                return json.load(inputfile)
        except BaseException as be:
            log.error(f"(JOB:{job_id}) confdata: failed to read job conf from shared fs. {be}")
            return None        

    # def create_job_subprocess(self, job_id: str, 
    #                           event_tool_config: EventToolConfig,
    #                           event_json: Dict[Any, Any],
    #                           max_ttl_s: Optional[int]
    #                                            ) -> Optional[int]:

    #     log.info(f"(JOB:{job_id}) process: creating as subprocess, pwd is '{os.getcwd()}'")

    #     log.debug(f"(JOB:{job_id}) process: event_json: '{event_json}'")

    #     log.debug(
    #         f"(JOB:{job_id}) process: event_tool_config: '{event_tool_config.__dict__}'"
    #     )

    #     log.info(
    #         f"(JOB:{job_id}) process: using '{event_tool_config.tool_to_run}'")

    #     started_at: Optional[int] = self._scheduler_ddb.update_job_as_started(
    #         job_id)

    #     if started_at is not None:
    #         self._send_tool_started(job_id=job_id,
    #                                 started_at=started_at,
    #                                 event_tool_config=event_tool_config)

    #     cmd: str = f"python {event_tool_config.tool_to_run}"

    #     completed: Optional[CompletedProcess[bytes]] = None

    #     input_dict: Dict[str, Any] = {
    #         "config": event_tool_config.tool_config,
    #         "event": event_json
    #     }  # dict format/convention used by framework api

    #     try:
    #         input_json: str = json.dumps(
    #             input_dict, cls=CustomJsonEncoder )# default=SchedulerService.__default_json)
    #         log.debug(
    #             f"(JOB:{job_id}) process: starting '{cmd}', passing '{input_json}'"
    #         )
    #         completed = subprocess.run(cmd.encode(encoding='utf-8', errors='strict'),
    #                                    capture_output=True,
    #                                    shell=True,
    #                                    timeout=max_ttl_s,
    #                                    input=input_json.encode(encoding='utf-8', errors='strict'))
    #     except BaseException as be:
    #         log.warning(
    #             f"(JOB:{job_id}) process: failed to actually start configured tool. {be}"
    #         )

    #     if completed is not None:

    #         exit_code: int = completed.returncode

    #         log.info(
    #             f"(JOB:{job_id}) process: tool exit code {exit_code}. '{event_tool_config.tool_to_run}'"
    #         )
    #         log.debug(f"(JOB:{job_id}) process: stdout:\n{completed.stdout.decode(encoding='utf-8', errors='ignore')}")
    #         log.debug(f"(JOB:{job_id}) process: stderr:\n{completed.stderr.decode(encoding='utf-8', errors='ignore')}")

    #         finished_at: Optional[
    #             int] = self._scheduler_ddb.update_job_as_finished(
    #                 job_id=job_id, exit_code=exit_code)

    #         if finished_at is not None:
    #             self._send_tool_finished(job_id=job_id,
    #                                      finished_at=finished_at,
    #                                      exit_code=exit_code,
    #                                      event_tool_config=event_tool_config)

    #     else:

    #         errored_at: Optional[
    #             int] = self._scheduler_ddb.update_job_as_errored(job_id=job_id)

    #         if errored_at is not None:
    #             self._send_tool_error(job_id=job_id,
    #                                   event_tool_config=event_tool_config)

    #         return None

    #     return exit_code

    def _job_container_name_from_job_id(self, job_id: str) -> str:
        return f"{job_id}"  # use same for now

    def _send_job_unrecoverable(self, job_id: str,
                                unrecoverable_at: int) -> None:
        # failed to be prepared, cant be recovered or retried
        self._send_job_event_status("(JOB:{job_id})", job_id, "unrecoverable", unrecoverable_at)        

    def _send_job_prepared(self, job_id: str, prepared_at: int) -> None:        
        # prepared ok, ready to start
        self._send_job_event_status("(JOB:{job_id})", job_id, "prepared", prepared_at)        

    def _send_job_unprepared(self, job_id: str, unprepared_at: int = time.time_ns()) -> None:        
        # failed preparation but will be retrying on next iteration
        self._send_job_event_status("(JOB:{job_id})", job_id, "unprepared", unprepared_at)        

    # def _send_tool_started(self, job_id: str, started_at: int,
    #                        event_tool_config: EventToolConfig) -> None:
    #     # TODO: TB: send aws eb event, log, dont raise exceptions
    #     # started process
    #     pass

    # def _send_tool_finished(self, job_id: str, finished_at: int,
    #                         exit_code: int,
    #                         event_tool_config: EventToolConfig) -> None:
    #     # TODO: TB: send aws eb event, log, dont raise exceptions
    #     # finished process, see exit code
    #     pass

    # def _send_tool_error(self, job_id: str,
    #                      event_tool_config: EventToolConfig) -> None:
    #     # TODO: TB: send aws eb event, log, dont raise exceptions
    #     # when attempted tool execution an error raised (tool not started)
    #     pass

    def process_due_job_requests(self) -> int:
        """Execute jobs as subprocess or as kubernetes jobs
        """

        due_jobs: Optional[
            List[JobRequest]] = self._scheduler_ddb.get_due_job_requests()

        if due_jobs is None:
            log.warning(
                f"(JOBS) failed to obtain the list of due job requests")
            return 0
        
        due_jobs_count: int = len(due_jobs)

        if due_jobs_count > self._settings.ESCH_EXEC_TOOL_K8_MAX_JOBREQUESTS:
            log.info(f"(JOBS) found {due_jobs_count} due jobs to run as local subprocesses but will enforce configured limit of {self._settings.ESCH_EXEC_TOOL_K8_MAX_JOBREQUESTS}")
            due_jobs = due_jobs[0:self._settings.ESCH_EXEC_TOOL_K8_MAX_JOBREQUESTS]            

        due_count: int = len(due_jobs)

        log.info(f"(JOBS) {due_count} due jobs to be processed as k8 jobs")

        prepared_count: int = 0
        failed_count: int = 0
        unrecoverable_count: int = 0
                
        for j in due_jobs:
            
            job_id: str = j.job_id

            created_k8_job: bool = False

            event_tool_config: Optional[
                EventToolConfig] = EventToolConfig.from_dict(
                    j.tool_config_json)

            if event_tool_config is None:
                log.warning(
                    f"(JOB:{job_id}) unrecoverable: unparseable tool config data"
                )
                unrecoverable_count = unrecoverable_count + 1
                unrecoverable_at: Optional[
                    int] = self._scheduler_ddb.update_job_as_unrecoverable(
                        job_id=job_id)
                if unrecoverable_at is not None:
                    self._send_job_unrecoverable(
                        job_id=job_id, unrecoverable_at=unrecoverable_at)
                continue

            if (event_tool_config.profile_id is None or len(event_tool_config.profile_id) == 0) and (event_tool_config.profile_path is None or len(event_tool_config.profile_path) == 0):
                log.warning(
                    f"(JOB:{job_id}) unrecoverable: tool config data has empty or missing profile_id and profile_path"
                )
                unrecoverable_count = unrecoverable_count + 1
                unrecoverable_at: Optional[
                    int] = self._scheduler_ddb.update_job_as_unrecoverable(
                        job_id=job_id)
                if unrecoverable_at is not None:
                    self._send_job_unrecoverable(
                        job_id=job_id, unrecoverable_at=unrecoverable_at)
                continue

            token: str = f"{APIKEY_PREFIX}{self._settings.MS_DEPS_APIKEY}"

            if event_tool_config.profile_id is not None and len(event_tool_config.profile_id) > 0:
                log.debug(f"(JOB:{job_id}) process: using profile_id {event_tool_config.profile_id} to retrieve dependencies")
                profile_packages: Optional[List[str]] = self._deps_remote_service.get_profile_packages(profile_id=event_tool_config.profile_id, token=token)
            else:
                log.debug(f"(JOB:{job_id}) process: using profile_path {event_tool_config.profile_path} to retrieve dependencies")
                profile_packages: Optional[List[str]] = self._deps_remote_service.get_path_packages(profile_path=event_tool_config.profile_path or '', token=token)

            if profile_packages is None:
                log.warning(
                    f"(JOB:{job_id}) unrecoverable: deps profile/packages missing for profile_id '{event_tool_config.profile_id}', profile_path {event_tool_config.profile_path}"
                )
                unrecoverable_count = unrecoverable_count + 1
                unrecoverable_at: Optional[
                    int] = self._scheduler_ddb.update_job_as_unrecoverable(
                        job_id=job_id)
                if unrecoverable_at is not None:
                    self._send_job_unrecoverable(
                        job_id=job_id, unrecoverable_at=unrecoverable_at)
                continue

            if not self.store_job_confdata(job_id=job_id, event_dict=j.event_json, tool_config=event_tool_config.__dict__, profile_packages=profile_packages):
                log.warning(
                    f"(JOB:{job_id}) unrecoverable: jobconf data failed to be persisted"
                )
                failed_count = failed_count + 1
                log.warning(
                    f"(JOB:{job_id}) unrecoverable: failed jobconf preparation before start")
                self._send_job_unprepared(job_id=job_id)
                continue
            
            created_k8_job = self.create_k8_job(job_id=job_id)

            if created_k8_job:
                log.info(f"(JOB:{job_id}) process: prepared to start. event={j.event_json}")
                prepared_count = prepared_count + 1
                prepared_at: Optional[
                    int] = self._scheduler_ddb.update_job_as_prepared(
                        job_id=job_id)
                if prepared_at is not None:
                    self._send_job_prepared(job_id=job_id,
                                            prepared_at=prepared_at)
            else:
                failed_count = failed_count + 1
                log.warning(
                    f"(JOB:{job_id}) process: failed preparation before start")
                self._send_job_unprepared(job_id=job_id)

        log.info(
            f"(JOBS) {due_count} jobs due: {prepared_count} prepared, {failed_count} not prepared, {unrecoverable_count} unrecoverable"
        )

        return prepared_count
    
    def mark_job_as_started(self, job_id: str, started_at: str) -> bool:
        log.debug(f"(JOB:{job_id}) marking as started since {started_at}")
        return self._scheduler_ddb.update_job_as_started(job_id=job_id, started_ns=int(started_at)) is not None
    
    def mark_job_as_finished(self, job_id: str, finished_at: str, exit_code: str) -> bool:
        log.debug(f"(JOB:{job_id}) marking as finished since {finished_at}, exit code was {exit_code}")
        return self._scheduler_ddb.update_job_as_finished(job_id=job_id, finished_ns=int(finished_at), exit_code=int(exit_code)) is not None

    def reschedule_job_request(self, job_id: str, due_at: str) -> Optional[JobRequest]:

        if not re.fullmatch('^\\d{19}$', due_at):
            log.warning(f"(JOB:{job_id}) reschedule ignored: due stamp is invalid: {due_at}")
            return None
        
        due_ns: int = int(due_at)
                
        current_request: Optional[JobRequest] = self._scheduler_ddb.get_job_request(job_id)

        if current_request is None:
            log.warning(f"(JOB:{job_id}) reschedule ignored: unable to find job request with id {job_id}")
            return None
        
        min_minutes_before_rescheduling: int = 1 # TODO: make this configurable, use min builtin default
        min_nanos_before_rescheduling: int = min_minutes_before_rescheduling * 60 * 10^9

        now_ns: int = time.time_ns() 

        if due_ns <= current_request.due_ns or due_ns < now_ns + min_nanos_before_rescheduling:
            log.warning(f"(JOB:{job_id}) reschedule ignored: requested due stamp {due_ns} is before current stamp or not in the future (now + {min_minutes_before_rescheduling}min)")
            return None
        
        new_job_id: Optional[str] = self._new_job_id(job_id)

        if new_job_id is None:
            log.warning(f"(JOB:{job_id}) reschedule ignored: job id format '{job_id}' is invalid, or unable to generate a new job id")
            return None

        # create a new job request reusing all data from current job request, except job_id and due_ns stamp
        return self._scheduler_ddb.new_job_request(job_id=new_job_id, due_ns=due_ns, triggering_event_type=current_request.triggering_event_type, tool_config_json=current_request.tool_config_json, event_json=current_request.event_json, scheduled_by_job=job_id)

    def update_health_tracking_file(self) -> None:
        health_tracking_file: str = self._settings.ESCH_EXEC_HEALTH_TRACKING_FILE

        if Utils.touch_file(health_tracking_file):
            log.debug(
                f"Updated timestamp of health tracking file {health_tracking_file}"
            )
        else:
            log.warning(
                f"Failed to update timestamp of health tracking file {health_tracking_file}"
            )

    def _new_job_id(self, job_id: str) -> Optional[str]:

        reschedule_match: Optional[Match[str]] = re.fullmatch('^(job-.*)(-r-\\w{5})$', job_id)

        if reschedule_match is None:

            simple_match: Optional[Match[str]] = re.fullmatch('^(job-.*)$', job_id)

            if simple_match is not None:
                return f"{job_id}-r-{Utils.randomword(5)}"
            
        else:

            return f"{reschedule_match.group(1)}-r-{Utils.randomword(5)}"
        
        return None
    
    def _send_job_event_status(self, log_id: str, job_id: str, progress_type: str, stamped_at: int) -> bool:
 
        eb_event_type: str = f"job-status-{progress_type}"
        eb_bus_name: str = self._settings.EB_SCHEDULER_BUS_NAME        
        eb_payload: str = json.dumps({ "job_id": job_id, "stamped_at": stamped_at })
        
        event_id: Optional[str] = self._eb.push_event(
                event_source=EB_EVENT_SOURCE_SCHEDULER,
                bus_name=eb_bus_name,
                event_type=eb_event_type,
                json_payload=eb_payload)
        
        if event_id is not None:
            log.info(f"{log_id} pushed wrapped event data as id '{event_id}' to event bus '{eb_bus_name} using type '{eb_event_type}'")
            return True
        
        return False