import re

CONFIG_ID_PREFIX: str = "cid_"

class ConfigName():
    """Represents a configuration name and how to validate such name.
    """

    @staticmethod
    def is_name_valid(name: str) -> bool:
        return re.fullmatch(
            "\\w[\\w-]*",
            name) is not None and not name.strip().startswith(CONFIG_ID_PREFIX) # config name should not start with cid_
