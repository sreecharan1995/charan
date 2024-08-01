from typing import Optional
from enum import Enum

class Division(Enum):
    """Represents one of the known division types.
    """
    
    TELEVISION = "television"
    FILM = "film"
    # STOCK = "stock"

    @staticmethod
    def get_division_from_text(text: str, exact_match: bool = False) -> Optional['Division']: 
        if text is None or len(text) == 0:
            return None

        text = text.strip().lower()

        if exact_match:
            if text == "film":
                return Division.FILM
        else:            
            if text.find("film") != -1:
                return Division.FILM

        if text == "television":
            return Division.TELEVISION

        # if text == "stock":
        #     return Division.STOCK

        return None
