# coding: utf-8

from typing import Any, Dict

from pydantic import BaseModel, Field

from common.domain.sg.shotgrid_event import ShotgridEvent

class ShotgridEventModel(BaseModel):
    """Model representing an event payload as received from shotgrid
    """

    data: Dict[str,Any] = Field(default={}, title='payload data of event', description='The payload data of the event', example="{}")

    def as_shotgrid_event(self) -> ShotgridEvent:
        return ShotgridEvent(self.data)

ShotgridEventModel.update_forward_refs()


