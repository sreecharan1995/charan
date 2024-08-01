from typing import List, Optional

import boto3  # type: ignore

from common.domain.mocked_event import MockedEvent
from common.logger import log
from common.service.aws.eb_settings import EbSettings

mocked_bus: List[MockedEvent] = []

class Eb:
    """Contains methods to interact with the aws event bus
    """

    settings: EbSettings

    def __init__(self, settings: EbSettings):

        self.settings = settings

        self.client = boto3.client(  #type: ignore
            "events",
            region_name=settings.EB_REGION_NAME,
            aws_access_key_id=settings.EB_ACCESS_KEY_ID,
            aws_secret_access_key=settings.EB_SECRET_ACCESS_KEY,
        )

    def push_event(self, event_source: str, bus_name: str, event_type: str, json_payload: str) -> Optional[str]:

        if self.settings.EB_MOCK_EVENTBUS:
            e = MockedEvent(bus_name=bus_name, event_type=event_type, payload=json_payload)
            mocked_bus.append(e)
            log.debug(f"[{bus_name}] *MOCKED* PUSHED EVENT: {e.str()}")
            return "012345678901234567890" # TODO: generate a random

        try:
            response = self.client.put_events(  #type: ignore
                Entries=[{
                    "Source":
                    event_source,
                    "DetailType":
                    event_type,
                    "Detail":
                    json_payload,
                    "EventBusName":
                    bus_name,
                }])
        except BaseException as be:
            log.error(f"[{bus_name}] FAILED TO PUSH EVENT. ERROR: {be}")
            return None
        
        log.debug(f"[{bus_name}] PUSHED EVENT PAYLOAD: {json_payload}")

        log.debug(f"[{bus_name}] PUSHING RESPONSE: {response}")

        entries: str = response.get('Entries', None) # type: ignore

        event_id: str = str(entries)

        log.debug(f"[{bus_name}] PUSING RESPONSE ENTRIES: {event_id}")

        return event_id
        