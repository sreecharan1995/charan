from datetime import datetime
from typing import Any, Dict
from common.domain.event_sources import EB_EVENT_SOURCE
from pydantic import BaseModel


class EventModel(BaseModel):
    """This model represents event data received from aws event bus.

    This is a general example of how this data looks like:
    
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

    id: str
    time: datetime
    source: str
    detail: Dict[str, Any]

    def bid(self) -> str:
        return f"[{EB_EVENT_SOURCE}:{self.id[0:8]}]"

EventModel.update_forward_refs()