from typing import Optional
from enum import Enum

class PathType(Enum):
    """Represents one of the valid resource path types used to differentiate "sequences" from "assets".

    A resource path referring to a sequence or asset has a specific structure including one of this words in its string representation.
    """
    
    SEQUENCE = "sequence"
    ASSET = "asset"

    @staticmethod
    def get_type_from_text(text : str) -> Optional['PathType']: 
        if text is None or len(text) == 0:
            return None

        text = text.strip().lower()

        if text == "sequence":
            return PathType.SEQUENCE

        if text == "asset":
            return PathType.ASSET

        return None
