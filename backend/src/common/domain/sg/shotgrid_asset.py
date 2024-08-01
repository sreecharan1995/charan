
from typing import Any, Dict, Optional

class ShotgridAsset():
    """Wraps a shotgrid asset data and methods to conveniently access some of it.
    """

    _dict: Dict[str, Any]

    def __init__(self, asset_dict: Dict[str,Any]) -> None:
        
        self._dict = asset_dict

    def get_id(self) -> Optional[int]:

        return self._dict.get("id",  None)
        
    def get_code(self) -> Optional[str]:

        return self._dict.get("code",  None)
    
    def get_type(self) -> Optional[str]:
    
        return self._dict.get("sg_asset_type", None)

    # def asset_dict(self) -> Dict[str,Any]:

    #     return self._dict
    


    