
from typing import Any, Dict, Optional

from common.domain.sg.shotgrid_task import ShotgridTask

class ShotgridPublishedFile():
    """Wraps a shotgrid publishedfile data and methods to conveniently access some of it.
    """

    _dict: Dict[str, Any]

    def __init__(self, publishedfile_dict: Dict[str,Any]) -> None:
        
        self._dict = publishedfile_dict
    
    def get_id(self) -> Optional[int]:
        return self._dict.get("id",  None)
    
    def get_task(self) -> Optional[ShotgridTask]:
        return ShotgridTask(self._dict.get("task", {}))
        


    