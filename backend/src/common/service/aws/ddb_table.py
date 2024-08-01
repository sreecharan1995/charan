
from typing import Any, Dict, List


class DdbTable:
    """Represents one of the dynamodb tables
    """

    _alias: str
    _name: str
    _attr_defs: List[Dict[str,str]] = []
    _key_schema: List[Dict[str,str]] = []
    _global_indexes: List[Any] = []
    _read_capacity: int
    _write_capacity: int

    def __init__(self, alias: str, name: str, attr_defs: List[Dict[str,str]], key_schema: List[Dict[str,str]] = [], global_indexes: List[Any] = [], read_capacity: int = 5, write_capacity: int = 5):

        self._alias = alias
        self._name = name
        self._attr_defs = attr_defs
        self._key_schema = key_schema
        self._global_indexes = global_indexes
        self._read_capacity = read_capacity
        self._write_capacity = write_capacity

    def get_alias(self) -> str:
        return self._alias
        
    def get_name(self) -> str:
        return self._name

    def get_key_schema(self) -> List[Dict[str,str]]:
        return self._key_schema

    def get_global_indexes(self) -> List[Any]:
        return self._global_indexes        

    def get_attr_defs(self) -> List[Dict[str,str]]:
        return self._attr_defs

    def get_read_capacity(self) -> int:
        return self._read_capacity

    def get_write_capacity(self) -> int:
        return self._write_capacity
