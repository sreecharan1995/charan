# coding: utf-8

import json
import hmac
import hashlib

from typing import Optional

from fastapi import (APIRouter, Body, HTTPException, Request, Response)

from common.domain.event_sources import SG_EVENT_SOURCE
from common.api.model.status_model import StatusModel
from common.domain.sg.shotgrid_event import ShotgridEvent
from common.logger import log
from sourcing.sourcing_settings import SourcingSettings
from sourcing.service.sourcing_service import SourcingService
from common.api.model.shotgrid_event_model import ShotgridEventModel
from sourcing import event_stats

router = APIRouter()
settings: SourcingSettings = SourcingSettings.load()

sourcing_service: SourcingService = SourcingService(settings)


@router.post(
    "/on-event",
    status_code=202,
    response_class=Response,
    responses={
        202: {
            "description": "Event received"
        },
        400: {
            "model": StatusModel,
            "description": "Bad request or signature"
        },
        422: {
            "model": StatusModel,
            "description": "Unable to process"
        },
        401: {
            "model": StatusModel,
            "description": "Unauthenticated"
        },
    },
    tags=["profiles"],
    summary="Receives an event from shotgrid webhook",
)
async def receive_a_shotgrid_event(
    request: Request,
    shotgrid_event_model: ShotgridEventModel = Body(
        None, description="The payload of shotgrid event"),
) -> None:
    """Receive events from shotgrid webhook and inject them into an internal aws event bus"""

    if shotgrid_event_model is None:
        raise HTTPException(status_code=400, detail="Bad request. Empty body.")

    json_body: str = json.dumps(shotgrid_event_model.dict())
        
    shotgrid_event: ShotgridEvent = shotgrid_event_model.as_shotgrid_event()

    event_id: Optional[str] = shotgrid_event.get_id()
    event_type: Optional[str] = shotgrid_event.get_type()
    event_site: Optional[str] = shotgrid_event.get_site()
    event_person: Optional[str] = shotgrid_event.get_person()

    log.debug(f"incoming data: {json_body}")

    if event_id is None:
        log.warning(
            f"rejecting data, is not an event or has no id: {json_body}")
        raise HTTPException(
            status_code=400,
            detail="Bad request. Event has no id or is not an event.")

    if event_type is None:
        log.warning(
            f"{shotgrid_event.get_log_id()} rejecting: has no type: {json_body}")
        raise HTTPException(
            status_code=400,
            detail="Bad request. Event has no type or is not an event.")
    
    if event_person is None:
        log.warning(
            f"{shotgrid_event.get_log_id()} rejecting: has no person: {json_body}")
        raise HTTPException(
            status_code=400,
            detail="Bad request. Event has no person id or is not an event.")

    signature: Optional[str] = request.headers.get("X-SG-SIGNATURE", None)

    verified_source: bool = False

    if signature is not None:
        request_body: str = (await request.body()).decode("utf-8")

        log.debug(f"{shotgrid_event.get_log_id()} incoming signature: '{signature}'")                
        
        sha1: str = hmac.new(
            settings.ESRC_SG_EVENT_SIGNATURE_TOKEN.encode(encoding='UTF-8'),
            request_body.encode('UTF-8'), hashlib.sha1).hexdigest()
        
        log.debug(f"{shotgrid_event.get_log_id()} calculated signature is 'sha1={sha1}'")

        if signature == f"sha1={sha1}":
            verified_source = True
        else:
            log.debug(
                f"{shotgrid_event.get_log_id()} signature verification failed: wrong token configured for source '{SG_EVENT_SOURCE}' or data is corrupted/tampered"
            )
    else:
        log.debug(
            f"{shotgrid_event.get_log_id()} signature verification not performed: no signature detected in headers for source '{SG_EVENT_SOURCE}'"
        )

    if not verified_source and settings.ESRC_REJECT_SG_EVENTS_WITHOUT_CORRECT_SIGNATURES:
        log.warning(
            f"{shotgrid_event.get_log_id()} rejecting event: signature verification failed: source '{SG_EVENT_SOURCE}' could not be verified")
        raise HTTPException(
            status_code=400,
            detail="Bad request. Signature missing or failed verification.")

    log.info(f"{shotgrid_event.get_log_id()} processing event of type '{event_type}', site '{event_site or ''}', person id '{event_person}'")

    event_stats.increment(event_type=event_type)

    if sourcing_service.send_sg_event(verified_source=verified_source, shotgrid_event=shotgrid_event):
        return

    raise HTTPException(status_code=400,
                        detail="Failed to process at this time")
