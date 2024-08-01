from typing import Any, Dict, Optional
from common.domain.build_info import BuildInfo
from common.api.model.event_model import EventModel
from common.build_settings import BuildSettings
from common.domain.event_sources import EB_EVENT_SOURCE

build_settings: BuildSettings = BuildSettings()
build_info: BuildInfo = BuildInfo(build_settings)

class AugmentedEvent():
    """Represents a wrapped event, potentially augmented with extra known data
    """

    id: str
    eb_id: Optional[str]
    source: str
    verified_source: bool
    proxy: Dict[str,Any]
    site: Optional[str]
    event: Dict[Any,Any]

    def __init__(self, id: str, source: str, verified_source: bool, site: Optional[str], event: Dict[str,Any]) -> None:
        self.id = id
        self.source = source
        self.verified_source = verified_source
        self.proxy = build_info.__dict__
        self.site = site
        self.event = event        
        return
    
    def uid(self) -> str:
        self_id: str = f"[{self.source.upper()}:{self.id}]"
        if self.eb_id is not None:
            return f"[{EB_EVENT_SOURCE}:{self.eb_id[0:8]}]{self_id}"
        else:
            return f"{self.id}"
        
    def normalized_job_id(self) -> str:

        job_name: str = f"{self.source.lower()}-{self.id}"

        job_name = job_name.replace(" ", "").replace(".", "-").replace("_", "-").lower()

        return f"job-{job_name}"


    @staticmethod
    def from_dict(data: Dict[str,Any]) -> 'AugmentedEvent':

        d_id: str = data.get("id", "")
        d_eb_id: str = data.get("eb_id", None)
        d_source: str = data.get("source", "")
        d_verified_source: bool = data.get("verified_source", "") 
        d_proxy: Dict[str,Any] = data.get("proxy", "")
        d_site: Optional[str] = data.get("site", None)
        d_event: Dict[Any,Any] = data.get("event", dict())

        augmented_event: AugmentedEvent = AugmentedEvent(id=d_id, source=d_source, verified_source=d_verified_source, site=d_site, event=d_event)

        augmented_event.eb_id = d_eb_id
        augmented_event.proxy = d_proxy

        return augmented_event        

    @staticmethod
    def from_event_model(event_model: EventModel) -> 'AugmentedEvent':

        d: Dict[str,Any] = event_model.dict()
        augmented_event = AugmentedEvent.from_dict(d.get("detail", dict()))
        augmented_event.eb_id = event_model.id

        return augmented_event