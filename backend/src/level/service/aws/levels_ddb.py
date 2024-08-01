import json
import time
from typing import Any, List, Optional

from boto3.dynamodb.conditions import Attr, Key  # type: ignore

from common.logger import log
from common.service.aws.base_ddb import BaseDdb
from common.service.aws.ddb_table import DdbTable
from level.domain.sync_request import SyncRequest
from level.level_settings import LevelSettings


class LevelsDdb(BaseDdb):
    """Provides the methods to operate on the dynamodb table holding data about sync requests and latest available tree
    """

    _level_settings: LevelSettings

    TABLE_SGTREE_ALIAS: str = "SGTREE"

    def __init__(self, settings: LevelSettings):

        self._level_settings = settings
        
        TABLE_SGTREE = DdbTable(self.TABLE_SGTREE_ALIAS, settings.current_sgtree_table(),
                                key_schema=[
                                    {
                                        "AttributeName": "catalog",
                                        "KeyType": "HASH"
                                    },
                                    {
                                        "AttributeName": "id",
                                        "KeyType": "RANGE"
                                    },
                                ],
                                attr_defs=[
                                    {
                                        "AttributeName": "catalog",
                                        "AttributeType": "S"
                                    },
                                    {
                                        "AttributeName": "id",
                                        "AttributeType": "N"
                                    },
                                ],
                                read_capacity=5,
                                write_capacity=5)

        super(LevelsDdb, self).__init__(settings,
                                        ddb_tables=[TABLE_SGTREE])

    def table_sgtree(self):
        return super().ddb_table(self.TABLE_SGTREE_ALIAS)

    def new_sync_request(self,
                         comment: Optional[str] = "") -> Optional[SyncRequest]:

        table = self.table_sgtree()

        now_ns: int = time.time_ns()

        response = table.put_item(
            Item={
                "catalog": self._level_settings.LVL_SYNC_DDB_TABLE_SGTREE_CATALOG,  # this is used as hash key (partition/catalog)
                "id": now_ns,  # this is used as range key (sorted for the same catalog)
                "comment": comment,  # empty comment by default
                "filename": "",  # empty means request is yet unfulfilled
            }
        )

        retries_left: int = 2

        while (
                retries_left > 0
        ):  # deal with fetches not yet returning a successfully created item

            dict = self.__get_sync_request(now_ns)

            if dict is None:
                log.warning(
                    f"Created sync request but still missing. id: '{id}'. response: '{json.dumps(response)}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return SyncRequest(
                    id=dict.get("id"),
                    comment=dict.get("comment"),
                    filename=dict.get("filename"),
                )

        return None

    def __get_sync_request(self, id: int) -> Optional[Any]:

        table = self.table_sgtree()        

        response = table.get_item(
            Key={
                "catalog":
                self._level_settings.LVL_SYNC_DDB_TABLE_SGTREE_CATALOG,
                "id": id
            })  

        dict: Optional[Any] = response.get("Item")  # type: ignore

        return dict

    def _get_sync_requests(self,
                           fulfilled: bool) -> Optional[List[SyncRequest]]:

        table = self.table_sgtree()

        try:
            response = table.query(  # type: ignore
                KeyConditionExpression=Key("catalog").eq( # type: ignore
                    self._level_settings.LVL_SYNC_DDB_TABLE_SGTREE_CATALOG
                ),  # type: ignore
                FilterExpression=Attr("filename").ne("") # type: ignore
                if fulfilled else Attr("filename").eq(""),  # type: ignore
                ScanIndexForward=False,
                # Limit=1, # TODO: Annoying: limit is applied before filters, so it fails to detect the latest fulfilled when younger outstanding request are found
            )
        except Exception as e:
            log.error(e)
            return None

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None or len(items) == 0:
            return None

        return list(
            map(
                lambda i: SyncRequest(id=i.get("id"),
                                      comment=i.get("comment"),
                                      filename=i.get("filename")), items))

        # item = items[0]

        # return SyncRequest(id=item.get("id"),
        #                    comment=item.get("comment"),
        #                    filename=item.get("filename"))

    def get_unfulfilled_sync_requests(self) -> Optional[List[SyncRequest]]:

        return self._get_sync_requests(False)

    def get_fulfilled_sync_requests(self) -> Optional[List[SyncRequest]]:

        return self._get_sync_requests(True)

    def get_last_fulfilled_request(self) -> Optional[SyncRequest]:

        fulfilled_requests: Optional[
            List[SyncRequest]] = self.get_fulfilled_sync_requests()

        if fulfilled_requests is None or len(fulfilled_requests) == 0:
            return None

        return fulfilled_requests[0]

    def update_request_filename(self, id: int, filename: str):
        
        table = self.table_sgtree()

        try:

            response = table.update_item(  # type: ignore
                Key={"catalog": self._level_settings.LVL_SYNC_DDB_TABLE_SGTREE_CATALOG, "id": id},
                UpdateExpression="set filename=:filename",
                ExpressionAttributeValues={":filename": filename},
                ReturnValues="ALL_NEW",
            )

            return True if response["Attributes"][
                "filename"] is not None else False

        except Exception as e:

            log.error(e)
            return False
