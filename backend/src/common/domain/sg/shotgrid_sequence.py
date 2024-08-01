
from typing import Any, Dict, List, Optional

from common.domain.sg.shotgrid_shot import ShotgridShot

class ShotgridSequence():
    """Wraps a shotgrid sequence data and methods to conveniently access some of it.
    """

    _dict: Dict[str, Any]

    def __init__(self, sequence_dict: Dict[str,Any]) -> None:
        
        self._dict = sequence_dict

    def get_id(self) -> Optional[int]:
        return self._dict.get("id", None)
    
    def get_code(self) -> Optional[str]:
        return self._dict.get("code", None)
    
    def get_shots(self) -> Optional[List[ShotgridShot]]:

        return list(map(lambda s: ShotgridShot(s), self._dict.get("shots", [])))                    
    


    