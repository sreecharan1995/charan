import sys
from functools import lru_cache

from pydantic import BaseSettings

from common.logger import log


class DdbSettings(BaseSettings):
    """Holds the env vars that refers to dynamodb configuration like aws keys, tables prefixes, etc.
    """

    # The following holds the aws credentials used when operating on dynamodb service
    DDB_REGION_NAME: str = "us-east-1"
    DDB_ACCESS_KEY_ID: str = ""
    DDB_SECRET_ACCESS_KEY: str = ""

    DDB_INIT: bool = True
    """Indicates wheter to perform table initialization or not
    """

    DDB_INIT_READONLY: bool = False
    """Indicates if during initialization, only an existence check is to be performed or tables must be created if not found
    """

    DDB_TABLES_USERID: str = "x"
    """Indiciates the prefix attached at the beginning of each table name.

    This is useful for developers while developing locally but also to differentiate uat from prod from dev tables.
    """

    def __init__(self):
        log.debug("Loading DDB settings")                
        super(DdbSettings, self).__init__()  # type: ignore

    def _current_tables_userid(self) -> str:
        return (
            f"{self.DDB_TABLES_USERID.strip()}"
            if self.DDB_TABLES_USERID.strip() != ""
            else "x"
        )

    def _pytest_suffix(self) -> str:
        return "-pytest" if "pytest" in sys.modules else ""

    def _table_name(self, table: str) -> str:
        return f"{self._current_tables_userid()}-{table}{self._pytest_suffix()}"
    
    @staticmethod
    @lru_cache()
    def load_ddb() -> 'DdbSettings':
        return DdbSettings()        
