from typing import Optional, List
from fastapi import APIRouter, Request, Response, HTTPException
from common.service.aws.k8 import K8
from common.logger import log
from common.domain.k8.pod import Pod
from common.domain.k8.job import Job
from scheduler.service.scheduler_service import SchedulerService
from scheduler.scheduler_settings import SchedulerSettings

router = APIRouter()

"""This API is for testing/debugging purposes, not for production
"""

scheduler_service = SchedulerService(settings=SchedulerSettings.load())

@router.post(
    "/resetjob/{job_id}",
    status_code=200,
    summary=
    "Reset the status execution for a job, so it can run again"
    )
async def resetjob(req: Request, job_id: str, res: Response):

    scheduler_service.reset_job_request(job_id)


@router.get(
    "/k8/pods",
    status_code=200,
    summary=
    "Listing all pods currently in the k8 cluster"
    )
async def k8_pods(req: Request, res: Response):

    k8: K8 = K8()

    pod_list: Optional[List[Pod]] = k8.list_pods()

    if pod_list is None:
        raise HTTPException(status_code=503, detail="Try again later")

    p: Pod

    for p in pod_list:
        log.info(f"pod: {p.name}, namespace: {p.namespace}, ip: {p.ip}")

@router.get(
    "/k8/pod/{pod_name}",
    status_code=200,
    summary=
    "Get the pod description from k8"
    )
async def k8_pod(req: Request, pod_name: str, res: Response):

    k8: K8 = K8()

    pod: Optional[Pod] = k8.get_pod(pod_name)

    if pod is None:
        raise HTTPException(status_code=404, detail="Not found")
    
    log.info(f"pod: {pod.name}, namespace: {pod.namespace}, ip: {pod.ip}, image(0): {pod.get_image_name()}")
    

@router.get(
    "/k8/jobs",
    status_code=200,
    summary=
    "Listing all jobs currently in the k8 cluster"
    )
async def k8_jobs(req: Request, res: Response):

    k8: K8 = K8()

    job_list: Optional[List[Job]] = k8.list_jobs()

    if job_list is None:
        raise HTTPException(status_code=503, detail="Try again later")

    j: Job

    for j in job_list:
        log.info(f"job: {j.name}, namespace: {j.namespace}, status: {j.get_status()}")
