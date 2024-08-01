# coding: utf-8

import json
from typing import Any, List, Dict, Optional

from common.service.aws.eb import Eb
from common.logger import log
from common.domain.event_sources import EB_EVENT_SOURCE_REZ_SERVICE
from rezv.domain.validation_result import ValidationResult
from rezv.rez_settings import RezSettings
from common.domain.mocked_event import MockedEvent

PROFILE_VALIDATION_COMPLETED: str = "profile-validation-completed"


mocked_bus: List[MockedEvent] = []


class EventsService:
    def __init__(self, settings: RezSettings = RezSettings.load()):

        self.eb = Eb(settings)
        self.settings = settings
        log.info("Events Service instantiated")

    def on_profile_validated(self, validation: ValidationResult) -> None:

        if validation is None:
            return

        message = validation.get_message()
        log.debug(f"validation result: {message}")

        if self._send_message(message, PROFILE_VALIDATION_COMPLETED) is None:
            raise Exception("Unable to send validation result")

    def _send_message(self, message: Dict[Any,Any], event_type: str) -> Optional[str]:

        if message is None:
            return None

        pl: str = json.dumps(message)
        
        return self.eb.push_event(
                bus_name=self.settings.current_validation_eventbus(),
                event_source=EB_EVENT_SOURCE_REZ_SERVICE,
                event_type=event_type,
                json_payload=pl
            )
