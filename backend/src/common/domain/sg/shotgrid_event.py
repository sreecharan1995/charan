
from typing import Any, Dict, Optional
from common.domain.event_sources import SG_EVENT_SOURCE

class ShotgridEvent():
    """Wraps a shotgrid event data and methods to conveniently access some of it.
    """

    _data: Dict[str, Any]
    _default_site: Optional[str]

    def __init__(self, data: Dict[str, Any], default_site: Optional[str] = None)-> None:
        self._data = data
        self._default_site = default_site

    def dict(self) -> Dict[str,Any]:
        return self._data

    def get_type(self) -> Optional[str]:

        if self._data is None:
            return None
        
        etype: str = self._data.get("event_type", "")

        return etype if len(etype) > 0 else None

    def get_changed_attr(self) -> Optional[str]:

        if self._data is None:
            return None
        
        eattr: str = self._data.get("attribute_name", "")

        return eattr if len(eattr) > 0 else None
    
    def get_project_id(self) -> Optional[int]:

        id: int = self._data.get("project", dict()).get("id", None)
        return id

    def get_site(self) -> Optional[str]:
        
        site: Optional[str] = self._data.get("event_site", self._default_site) # in case it comes from shotgrid event metadata (adjust key in that case)

        if site is None:
            return None

        return site if len(site) > 0 else None    

    def get_person(self) -> Optional[str]:

        return "unknown@unknown.com"  # TODO: TBI
    
    def get_id(self) -> Optional[str]:

        if self._data is None:
            return None
        
        id: str = self._data.get("id", "") 

        return id if len(id) > 0 else None
    
    def get_log_id(self) -> str:

        return f"[{SG_EVENT_SOURCE.upper()}:{self.get_id() or '???'}]"
