
from typing import Any, Dict, Optional

class ShotgridShot():
    """Wraps a shotgrid shot data and methods to conveniently access some of it.
    """

    _dict: Dict[str, Any]

    def __init__(self, shot_dict: Dict[str,Any]) -> None:
        
        self._dict = shot_dict

    def get_id(self) -> Optional[int]:
        return self._dict.get("id", None)
        
    def get_name(self) -> Optional[str]:
        return self._dict.get("name", None)
    


    