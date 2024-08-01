from typing import List, Optional
from enum import Enum

class Site(Enum):
    """Represents one of the valid known sites used in resource levels or path representations as strings.
    """
    
    GLOBAL = "Global"
    MUMBAI = "Mumbai"
    TORONTO = "Toronto"    

    @classmethod
    def list(cls) -> List['Site']:
        return [Site.GLOBAL, Site.MUMBAI, Site.TORONTO]

    @staticmethod
    def get_site_from_text(text : str) -> Optional['Site']: 
        if text is None or len(text) == 0:
            return None

        text = text.strip().lower()

        if text.find("global") != -1:
            return Site.GLOBAL

        if text == "mumbai":
            return Site.MUMBAI

        if text == "toronto":
            return Site.TORONTO

        return None
