from typing import Any, Dict

from common.logger import log
from fastapi import APIRouter, Request, Response  # noqa: F401
from rezv.domain.validation_request import ValidationRequest, ValidationRequestException
from rezv.service.rez_service import RezService

router = APIRouter()

rez_service = RezService()


@router.post(
    "/on-event",
    status_code=202,
    summary="Entry point for package resolution requests. Receives and processes a message requesting "
    "resolution of a set of packages."
)
async def on_event(req: Request, event: Dict[Any, Any], res: Response):
    """
        Sample event
        {
      "version": "0",
      "id": "b0f986e6-93f9-ef78-f8e1-d9f029e5b0a9",
      "detail-type": "profile-validation-request",
      "source": "dependency-service",
      "account": "301653940240",
      "time": "2022-07-12T18:42:50Z",
      "region": "us-east-1",
      "resources": [],
      "detail": {
        "id": "profile_drbrhqekihmx",
        "path": "/",
        "name": "root",
        "description": "root profile",
        "created_at": "2022-Jul-12T18:42:50",
        "profile_status": "pending",
        "packages": [],
        "bundles": [],
        "comments": []
      }
    }
    """
    try:
        log.debug("Received event: %s", event)
        vreq = ValidationRequest(event)
        rez_service.build_cache(vreq)
    except ValidationRequestException as vre:
        log.error(vre)
        res.status_code = 422
        pass
