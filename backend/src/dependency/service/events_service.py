# coding: utf-8

import json
from typing import List, Optional

from common.domain.event_sources import EB_EVENT_SOURCE_VALIDATION_SERVICE
from common.domain.mocked_event import MockedEvent
from common.service.aws.eb import Eb
from dependency.api.model.full_profile_model import FullProfileModel
from dependency.dependency_settings import DependencySettings

PROFILE_VALIDATION_REQUEST: str = "profile-validation-request"

mocked_bus: List[MockedEvent] = []


class EventsService:
    """Contains methods to properly generate validation events for a profile and possibly its descendants profiles.

    Events may be mocked, which is a behaviour configured in settings.
    """

    def __init__(self,
                 settings: DependencySettings = DependencySettings.load()):

        self.eb = Eb(settings)
        self.settings = settings

    def on_profile_validate(
            self, effective_profile: Optional[FullProfileModel]) -> bool:

        if effective_profile is None:
            return False

        et: str = PROFILE_VALIDATION_REQUEST
        pl: str = json.dumps(effective_profile.dict())

        if not self.eb.push_event(
                bus_name=self.settings.current_validation_eventbus(),
                event_source=EB_EVENT_SOURCE_VALIDATION_SERVICE,
                event_type=et,
                json_payload=pl):
            raise Exception("Unable to push event to request validation")

        return True
