from typing import Optional
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.sg.shotgrid_event import ShotgridEvent

from common.logger import log
from common.domain.event_sources import SG_EVENT_SOURCE, EB_EVENT_SOURCE_SCHEDULER_JOB
from common.api.model.event_model import EventModel
from fastapi import APIRouter, Request, Response, HTTPException
from common.service.sg import shotgrid_service
from common.utils import Utils
from scheduler.domain.job_event import JobEvent
from scheduler.domain.job_request import JobRequest
from scheduler.service.scheduler_service import SchedulerService
from scheduler.scheduler_settings import SchedulerSettings
from common.domain.event_sources import EB_EVENT_SOURCE_SOURCING_SERVICE
from common.domain.augmented_event import AugmentedEvent
from scheduler.domain.event_tool_config import EventToolConfig
from common.service.sg.shotgrid_service import ShotgridService

router = APIRouter()

settings = SchedulerSettings.load()
scheduler_service = SchedulerService(settings)
shotgrid_service = ShotgridService(settings)

@router.post(
    "/on-event",
    status_code=202,
    summary=
    "Entry point for tool scheduling requests. Receives and processes a message requesting "
    "execution of a tool at a certain time.")
async def on_event(req: Request, event_model: EventModel, res: Response):
    """Entry point for tool scheduling requests. Receives and processes a message requesting execution of a tool.

    Sample event 
    {
        "version": "0",
        "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
        "detail-type": "Shotgun_Task_new",
        "source": "sourcing-service",
        "account": "111122223333",
        "time": "2017-12-22T18:43:48Z",
        "region": "us-east-1",
        "resources": [
            "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        ],
        "detail": {
            "id": "96781.3080.0",
            "source": "sg",
            "verified_source": false,
            "proxy": {
            "build_id": "815",
            "build_date": "2023-01-12 13:57:52 EST",
            "build_hash": "1bd0fb5bb323dd53a5651a649a8dea6cc2fda9d4",
            "build_link": "https://bitbucket.org/spinvfx/spin_microservices/pipelines/results/815"
            },
            "site": "",
            "event": {
                "id": "96781.3080.0",
                "meta": {
                "type": "attribute_change",
                "entity_id": 1246,
                "new_value": "*Add fog and mist with depth",
                "old_value": "*Add fog and mist.",
                "entity_type": "Asset",
                "attribute_name": "description",
                "field_data_type": "text"
                },
                "user": {
                "id": 88,
                "type": "HumanUser"
                },
                "entity": {
                "id": 1246,
                "type": "Shot"
                },
                "project": {
                "id": 666,
                "type": "Project"
                },
                "operation": "update",
                "created_at": "2022-02-01 20:53:08.523887",
                "event_type": "Shotgun_Task_new",
                "delivery_id": "3a5de4ee-8f05-4eac-b537-611e845352fc",
                "session_uuid": "dd6a1d6a-83a0-11ec-8826-0242ac110006",
                "attribute_name": "description",
                "event_log_entry_id": 545175
            },
            "timestamp": "2022-02-01T20:53:09Z"
        }
        }    
    """
    try:
        log.debug(f"incoming: {event_model.dict()}")

        if event_model.id is None:
            log.warning(f"rejecting: has no id or not a bus event'")
            raise HTTPException(status_code=422, detail="Bus event has no id or not an event")

        if not event_model.source == EB_EVENT_SOURCE_SOURCING_SERVICE:
            log.warning(f"{event_model.bid()} rejecting: not from expected source '{EB_EVENT_SOURCE_SOURCING_SERVICE}', but from '{event_model.source}'")
            raise HTTPException(status_code=422, detail="Bus event source is not the expected")

        augmented_event: AugmentedEvent = AugmentedEvent.from_event_model(event_model)
 
        if augmented_event is None:
            log.warning(
                f"{event_model.bid()} rejecting: wrapped data is not an augmented event"
            )
            raise HTTPException(status_code=422, detail="Bus event data is unusable. No augmented event wrapped.")        

        if augmented_event.id is None or len(augmented_event.id) == 0:
            log.warning(
                f"{event_model.bid()} rejecting: wrapped augmented event: has no id"
            )
            raise HTTPException(status_code=422, detail="Bus event data is unusable. Wrapped augmented event has no id.")            
        
        if not augmented_event.source == SG_EVENT_SOURCE:
            log.warning(
                f"{augmented_event.uid()} rejecting: not from the expected '{SG_EVENT_SOURCE}' source"
            )
            raise HTTPException(status_code=422, detail="Bus event data is unusable. Wrapped augmented event not from the expected source.") 
        
        sg_event: ShotgridEvent = ShotgridEvent(augmented_event.event, default_site=settings.ESCH_SG_DEFAULT_SITE)

        event_type: Optional[str] = sg_event.get_type()        

        if event_type is None:
            log.warning(
                f"{augmented_event.uid()} dropping: no type specified"
            )
            return

        event_person: Optional[str] = sg_event.get_person()

        if event_person is None:
            log.warning(
                f"{augmented_event.uid()} dropping: has no user id"
            )
            return        

        event_site: Optional[str] = sg_event.get_site()

        if event_site is None:
            log.warning(
                f"{augmented_event.uid()} dropping: has no site (and no default is set)"
            )
            return        

        log.info(f"{augmented_event.uid()} processing event of type '{event_type}', site '{event_site or ''}', person id '{event_person}'")

        parsed_level_path: Optional[ParsedLevelPath] = shotgrid_service.get_event_level(sg_event)

        if parsed_level_path is None:
            log.warning(
                f"{augmented_event.uid()} dropping: unable to determine event level path"
            )
            return        

        level_path: LevelPath = parsed_level_path.to_level_path()
        event_path: str = level_path.get_path()

        event_tool_config: Optional[EventToolConfig] = scheduler_service.lookup_config(event_type=event_type, event_path=event_path, event_person=event_person)

        if event_tool_config is None:
            log.warning(
                f"{augmented_event.uid()} dropping: no tool configuration found for event type '{event_type}'"
            )
            return
        
        if event_tool_config.profile_path is None or len(event_tool_config.profile_path) == 0:
            event_tool_config.profile_path = event_path
        
        log.debug(f"{augmented_event.uid()} tool config: {event_tool_config.__dict__}")

        if scheduler_service.register(augmented_event=augmented_event, triggering_event_type=event_type, event_tool_config=event_tool_config):
            log.info(f"{augmented_event.uid()} registered for execution" )
        else:
            log.warning(f"{augmented_event.uid()} failed to register for execution" )
        
    except HTTPException as he:    
        res.status_code = he.status_code
    except BaseException as e:
        log.error(e)
        res.status_code = 503

@router.post(
    "/on-job-event",
    status_code=202,
    summary=
    "Entry point for events regarding scheduled job progress, like when it was started or if it finishes.")
async def on_job_event(req: Request, event_model: EventModel, res: Response):
    """Entry point for events regarding scheduled job progress, like when it was started or if it finishes.

    Sample of details wrapped in aws event details property:
    {
      { "job_id": "job-sg-4363656-343-0", "finished_at": "1677777888", "exit_code": "0" }'
    }
    """
    try:
        log.debug(f"incoming: {event_model.dict()}")

        if event_model.id is None:
            log.warning(f"rejecting: has no id or not a bus event'")
            raise HTTPException(status_code=422, detail="Bus event has no id or not an event")

        if not event_model.source == EB_EVENT_SOURCE_SCHEDULER_JOB:
            log.warning(f"{event_model.bid()} rejecting: not from expected source '{EB_EVENT_SOURCE_SCHEDULER_JOB}', but from '{event_model.source}'")
            raise HTTPException(status_code=422, detail="Bus event source is not the expected")

        job_event: JobEvent = JobEvent.from_dict(event_model.detail)
    
        if job_event.job_id is None:
            log.warning(f"{event_model.bid()} rejecting: wrapped job_event does not have a job_id")
            raise HTTPException(status_code=422, detail="Bus event wrapped data is invalid")

        if job_event.is_started_event():
            log.info(f"(JOB:{job_event.job_id}) RECV STARTED EVENT - {job_event.started_at}")
            scheduler_service.mark_job_as_started(job_event.job_id, job_event.started_at or "0")
        elif job_event.is_finished_event():
            log.info(f"(JOB:{job_event.job_id}) RECV FINISHED EVENT - {job_event.finished_at} - exit code {job_event.exit_code}")            
            scheduler_service.mark_job_as_finished(job_event.job_id, job_event.finished_at or "0", job_event.exit_code if job_event.exit_code is not None else "-9999999")
        elif job_event.is_reschedule_event():
            log.info(f"(JOB:{job_event.job_id}) RECV RESCHEDULED EVENT - {job_event.due_at}")            
            new_job_request: Optional[JobRequest] = scheduler_service.reschedule_job_request(job_event.job_id, str(job_event.due_at) if job_event.due_at is not None else "-8888888")
            if new_job_request is None:
                raise HTTPException(status_code=400, detail="Unable to reschedule. Invalid or inconsistent due time stamps")
            else:
                log.info(f"(JOB:{job_event.job_id}) re-scheduled as new job request, job id is {new_job_request.job_id}, due_ns is {new_job_request.due_ns} ({Utils.get_date_time(new_job_request.due_ns)})") 
        else:
            log.warning(f"{event_model.bid()} rejecting: wrapped job_event is invalid or unknown")
            raise HTTPException(status_code=422, detail="Bus event wrapped data is invalid or unknown")
        
    except HTTPException as he:    
        res.status_code = he.status_code
    except BaseException as e:
        log.error(f"Unexpected error {e}")
        res.status_code = 503
        
