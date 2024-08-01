from typing import List

from common.logger import log
from common.service.aws.ddb_client import DdbClient
from common.service.aws.ddb_settings import DdbSettings
from common.service.aws.ddb_table import DdbTable


class DdbBootstrapper:
    """Contains internally used methods to create or destroy dynamodb collections"""

    _settings: DdbSettings
    _ddb_client: DdbClient
    _ddb_tables: List[DdbTable]
    _init: bool
    _init_read_only: bool


    def __init__(self, settings: DdbSettings, ddb_client: DdbClient, ddb_tables: List[DdbTable]) -> None:

        self._settings = settings
        self._ddb_client = ddb_client
        self._ddb_tables = ddb_tables
        self._init = settings.DDB_INIT
        self._init_read_only = settings.DDB_INIT_READONLY

    def create_tables(self) -> bool:

        if not self._init:
            log.info(f"Skipping dynamodb tables creation/check")
            return True
        else:
            if not self._init_read_only:
                log.info(
                    f"Performing dynamodb tables existence check and creation if required"
                )
            else:
                log.info(f"Performing dynamodb tables existence check only")

        table: DdbTable

        success: bool = True

        for table in self._ddb_tables:

            exists: bool

            try:
                exists = self._ddb_client.exists_table(table.get_name())
            except Exception as e:
                log.error(f"Unable to check for table '{table.get_name()}' existence: {e}")
                success = False
                continue

            if not exists:

                if not self._init_read_only:
                    log.info(f"Creating table '{table.get_name()}'")
                    try:
                        self._ddb_client.create_table(table)
                    except Exception as ce:
                        log.error(f"Unable to create table {table.get_name()}: {ce}")
                        success = False
                        continue
                else:
                    log.error(f"Missing table '{table.get_name()}'")
                    success = False
                    continue

            else:
                log.info(f"Found table '{table.get_name()}'")

        return success

    def delete_tables(self) -> bool:

        if not self._init:
            log.info(f"Skipping dynamodb tables deletion because initialization is disabled in config")
            return True
        
        if self._init_read_only:
            log.info(f"Skipping dynamodb tables deletion in readonly mode")
            return True

        success: bool = True

        for table in self._ddb_tables:

            exists: bool

            try:
                exists = self._ddb_client.exists_table(table.get_name())
            except Exception as e:
                log.error(f"Unable to check for table '{table.get_name()}' existence: {e}")
                success = False
                continue

            if exists:
                try:
                    self._ddb_client.delete_table(table.get_name())
                except Exception as ce:
                    log.error(f"Unable to delete table {table.get_name()}: {ce}")
                    success = False
                    continue
            else:
                log.error(f"Missing table '{table.get_name()}'")
                success = False
                continue
        
        return success
