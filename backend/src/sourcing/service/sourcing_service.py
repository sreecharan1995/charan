# coding: utf-8

import json
from typing import Optional

from common.domain.augmented_event import AugmentedEvent
from common.domain.event_sources import EB_EVENT_SOURCE_SOURCING_SERVICE, SG_EVENT_SOURCE
from common.domain.sg.shotgrid_event import ShotgridEvent
from common.logger import log
from common.service.aws.eb import Eb
from sourcing.sourcing_settings import SourcingSettings


class SourcingService:
    """Contains methods to inject shotgrid events and other kind of events into the internal aws event bus.

    Events may be mocked, which is a behaviour configured in settings.
    """

    def __init__(self, settings: SourcingSettings = SourcingSettings.load()):

        self.eb = Eb(settings)
        self.settings = settings

    def send_sg_event(self, verified_source: bool, shotgrid_event: ShotgridEvent) -> bool:

        event_id: Optional[str] = shotgrid_event.get_id()

        if event_id is None:
            return False

        augmented_event: AugmentedEvent = AugmentedEvent(
            id=event_id,
            source=SG_EVENT_SOURCE,
            verified_source=verified_source,
            site=shotgrid_event.get_site(),
            event=shotgrid_event.dict())

        return self._send_event(log_id=shotgrid_event.get_log_id(), augmented_event=augmented_event)

    def _send_event(self, log_id: str, augmented_event: Optional[AugmentedEvent]) -> bool:

        if augmented_event is None:
            return False    
        
        eb_bus_name: str = self.settings.current_sourcing_eventbus()
        eb_event_type: str = self._get_eb_event_type_by_source(augmented_event.source)
        eb_payload: str = json.dumps(augmented_event.__dict__)

        event_id: Optional[str] = self.eb.push_event(
                event_source=EB_EVENT_SOURCE_SOURCING_SERVICE,
                bus_name=eb_bus_name,
                event_type=eb_event_type,
                json_payload=eb_payload)
        
        if event_id is not None:
            log.info(f"{log_id} pushed wrapped event data as id '{event_id}' to event bus '{eb_bus_name} using type '{eb_event_type}'")
            return True
        
        return False
    
    def _get_eb_event_type_by_source(self, source: str) -> str:

        return f"event-type-{source}"                