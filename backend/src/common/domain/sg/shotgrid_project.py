
from typing import Any, Dict, Optional

class ShotgridProject():
    """Wraps a shotgrid project data and methods to conveniently access some of it.
    """

    _dict: Dict[str, Any]

    def __init__(self, project_dict: Dict[str,Any]) -> None:
        
        self._dict = project_dict
    
    def get_id(self) -> Optional[int]:
        return self._dict.get("id",  None)
    
    def get_name(self) -> Optional[str]:

        return self._dict.get("name",  None)
    
    def get_division_name(self) -> Optional[str]:
        
        return self._dict.get("sg_type", None)
    
    def get_site(self) -> Optional[str]:

        # TODO: TBI
        return self._dict.get("meta", {}).get("site", None)
    
    def project_dict(self) -> Dict[str,Any]:
        return self._dict


    