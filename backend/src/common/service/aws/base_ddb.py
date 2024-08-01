
from typing import List, Optional

from common.service.aws.ddb_bootstrapper import DdbBootstrapper
from common.service.aws.ddb_client import DdbClient
from common.service.aws.ddb_settings import DdbSettings
from common.service.aws.ddb_table import DdbTable


class BaseDdb:
    """Base class for all "ddb" classes representing collections in dynamodb and providing common methods for them.
    """

    _settinggs: DdbSettings
    _ddb_client: DdbClient
    _ddb_bootstrapper: DdbBootstrapper
    _ddb_tables: List[DdbTable]    
    
    def __init__(self, settings: DdbSettings, ddb_tables: List[DdbTable]):

        self._settings = settings
        self._ddb_tables = ddb_tables
        self._ddb_client = DdbClient(settings)
        self._ddb_bootstrapper = DdbBootstrapper(settings, self._ddb_client, ddb_tables)

    def ddb_table(self, table_alias: str):

        ddb_table: DdbTable = self.table_by_alias(table_alias)
        
        return self._ddb_client.resource(ddb_table.get_name()) 

    def ddb_client(self):

        return self._ddb_client.client()

    def create_tables(self) -> bool:
        return self._ddb_bootstrapper.create_tables()

    def delete_tables(self) -> bool:
        return self._ddb_bootstrapper.delete_tables()

    def table_by_alias(self, table_alias: str) -> DdbTable:

        table: Optional[DdbTable] = self.__table_by_alias(table_alias)

        if table is None:
            raise Exception(f"Table not found using alias {table_alias}")

        return table

    def table_name(self, table_alias: str) -> str:

        return self.table_by_alias(table_alias).get_name()

    def __table_by_alias(self, table_alias: str) -> Optional[DdbTable]:

        t: DdbTable

        for t in self._ddb_tables:
            if t.get_alias() == table_alias:
                return t

        return None
    