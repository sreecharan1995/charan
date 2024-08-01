import json
from decimal import Decimal
from typing import Any

class CustomJsonEncoder(json.JSONEncoder):
    """Used to convert to valid json some Decimal representations when converting from dicts.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            if str(o).find(".") == -1:
                return int(o)
            else:
                return str(o)
        return super(CustomJsonEncoder, self).default(o)

    # @staticmethod
    # def __default_json(t: Any) -> Any:
    #     if type(t) is Decimal:
    #         return t
    #     return f"{t}"