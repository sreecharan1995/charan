
from typing import Any, Dict, List

import boto3  # type: ignore
from boto3.dynamodb.conditions import Attr, Key  # type: ignore

from common.logger import log
from common.service.aws.ddb_settings import DdbSettings
from common.service.aws.ddb_table import DdbTable


class DdbClient:
    """Represents and wraps a dyanmodb client to operate on resources like tables (collections)
    """

    _settings: DdbSettings
    _resource: Any
    _client: Any

    def __init__(self, settings: DdbSettings):

        self._settings = settings
        self._resource = boto3.resource(  # type: ignore
            "dynamodb",
            region_name=self._settings.DDB_REGION_NAME,
            aws_access_key_id=self._settings.DDB_ACCESS_KEY_ID,
            aws_secret_access_key=self._settings.DDB_SECRET_ACCESS_KEY,
        )
        self._client = boto3.client(  # type: ignore
            "dynamodb",
            region_name=self._settings.DDB_REGION_NAME,
            aws_access_key_id=self._settings.DDB_ACCESS_KEY_ID,
            aws_secret_access_key=self._settings.DDB_SECRET_ACCESS_KEY,
        )

    def resource(self, table_name: str) -> Any:
        return self._resource.Table(table_name)

    def client(self) -> Any:
        return self._client

    def create_table(self, table: DdbTable):
        return self._create_table(table.get_name(), table.get_key_schema(), table.get_attr_defs(), table.get_read_capacity(), table.get_write_capacity(), table.get_global_indexes())

    def _create_table(
        self, table_name: str, key_schema: List[Dict[str,str]], attr_def: List[Dict[str,str]], read_capacity: int = 5, write_capacity: int = 5, global_indexes: List[Dict[str,Any]] = []
    ):

        log.debug(f"Creating {table_name}")

        if len(global_indexes) > 0:
            table = self._resource.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attr_def,
                ProvisionedThroughput={
                    "ReadCapacityUnits": read_capacity,
                    "WriteCapacityUnits": write_capacity,
                },
                GlobalSecondaryIndexes=global_indexes
            )
        else: # unable to pass empty list or None for global indexes, so removing from args
            table = self._resource.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attr_def,
                ProvisionedThroughput={
                    "ReadCapacityUnits": read_capacity,
                    "WriteCapacityUnits": write_capacity,
                }
            )

        table.wait_until_exists()

    def delete_table(self, table_name: str):
        if table_name.find("-pytest") == -1:
            raise ValueError(
                "Refusing to delete a table which does not seem a temporary table used by pytests"
            )        
        table = self._resource.Table(table_name)
        log.debug(f"Deleting {table_name}")
        table.delete()        
        table.wait_until_not_exists() 
        

    def exists_table(self, table_name: str) -> bool:

        log.debug(f"Fetching tables listing")
        table_names = [t.name for t in self._resource.tables.all()]

        if table_name in table_names:
            return True

        return False
