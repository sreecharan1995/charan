import re

from common.domain.config_name import ConfigName, CONFIG_ID_PREFIX


class ConfigItem:
    """Represents a config item that is persisted o recovered from persistence.
    """
    
    id: str
    name: str
    path: str
    description: str
    inherits: bool
    active: int
    created: int
    updated: int
    created_by: str

    def __init__(self, id: str, path: str, name: str, description: str, inherits: bool, active: int, created: int, updated: int, created_by: str):
        
        self.id = id
        self.name = name
        self.path = path
        self.description = description
        self.inherits = inherits
        self.active = active
        self.created = created
        self.updated = updated
        self.created_by = created_by

    @staticmethod
    def is_id_valid(id: str) -> bool:
        return id is not None and re.fullmatch(f"{CONFIG_ID_PREFIX}\\w{'{24}'}", id) is not None

    @staticmethod
    def is_name_valid(name: str, non_exact_match: bool = False) -> bool:

        if name is not None and non_exact_match:
            if name.startswith("~"):
                if len(name) == 1:
                    return True
                name = name[1:]

        return name is not None and ConfigName.is_name_valid(name)