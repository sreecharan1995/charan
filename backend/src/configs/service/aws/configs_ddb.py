import json
import time
from typing import Any, List, Optional, Tuple

from common.api.utils import Utils as ApiUtils
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from common.logger import log
from common.service.aws.base_ddb import BaseDdb
from common.service.aws.ddb_table import DdbTable
from common.utils import Utils
from configs.configs_settings import ConfigsSettings
from configs.domain.config_item import CONFIG_ID_PREFIX, ConfigItem

# from boto3.dynamodb.conditions import Attr, Key  # type: ignore


class ConfigsDdb(BaseDdb):
    """Provides the methods to access the data on the dynamodb table used for config item storage
    """

    TABLE_CONFIGS_ALIAS: str = "CONFIGS"
    TABLE_CONFIGS_INDEX_PATH: str = "index_path"
    TABLE_CONFIGS_INDEX_NAME: str = "index_name"

    def __init__(self,
                 settings: ConfigsSettings):

        TABLE_CONFIGS = DdbTable(self.TABLE_CONFIGS_ALIAS,
                                 settings.current_configs_table(),
                                 attr_defs=[
                                     {
                                         "AttributeName": "id",
                                         "AttributeType": "S"
                                     },
                                     {
                                         "AttributeName": "config_name",
                                         "AttributeType": "S"
                                     },
                                     {
                                         "AttributeName": "level_path",
                                         "AttributeType": "S"
                                     },
                                     {
                                         "AttributeName": "active",
                                         "AttributeType": "N"
                                     },
                                 ],
                                 key_schema=[
                                     {
                                         "AttributeName": "id",
                                         "KeyType": "HASH"
                                     },
                                 ],
                                 global_indexes=[{
                                     "IndexName":
                                     self.TABLE_CONFIGS_INDEX_PATH,
                                     "KeySchema": [{
                                         "AttributeName": "level_path",
                                         "KeyType": "HASH"
                                     }, {
                                         "AttributeName": "config_name",
                                         "KeyType": "RANGE"
                                     }],
                                     "Projection": {
                                         "ProjectionType": "ALL"
                                     },
                                     "ProvisionedThroughput": {
                                         "ReadCapacityUnits": 5,
                                         "WriteCapacityUnits": 5,
                                     }
                                 }, {
                                     "IndexName":
                                     self.TABLE_CONFIGS_INDEX_NAME,
                                     "KeySchema": [{
                                         "AttributeName": "config_name",
                                         "KeyType": "HASH"
                                     }, {
                                         "AttributeName": "active",
                                         "KeyType": "RANGE"
                                     }],
                                     "Projection": {
                                         "ProjectionType": "ALL"
                                     },
                                     "ProvisionedThroughput": {
                                         "ReadCapacityUnits": 5,
                                         "WriteCapacityUnits": 5,
                                     }
                                 }],
                                 read_capacity=5,
                                 write_capacity=5)

        super(ConfigsDdb, self).__init__(settings,
                                         ddb_tables=[TABLE_CONFIGS])

    def table_configs(self):
        return super().ddb_table(self.TABLE_CONFIGS_ALIAS)

    def create_config(self, path: str, name: str, description: Optional[str], inherits: Optional[bool], created_by: str) -> Optional[ConfigItem]:

        table = self.table_configs()

        id: str = f"{CONFIG_ID_PREFIX}{Utils.randomid(24)}"

        now: int = time.time_ns()

        response = table.put_item(Item={
            "id": id,
            "level_path": path,
            "config_name": name,
            "config_name_searchable": name.lower(),
            "description": description or '',
            "inherits": 1 if inherits is None or inherits else 0,
            "active": 0,
            "created_by": created_by,
            "created": now,
            "updated": now
        })

        retries_left: int = 2

        while (
                retries_left > 0
        ):  # deal with fetches not yet returning a successfully created item

            config_item: Optional[ConfigItem] = self.get_config_by_id(id)

            if config_item is None:
                log.warning(
                    f"Created config but still missing. id: '{id}'. response: '{json.dumps(response)}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return config_item

        return None

    def patch_config(self, id: str, path: str, name: str, description: str, inherits: bool, active: int) -> Optional[ConfigItem]:

        table = self.table_configs()

        response = table.update_item(  # type: ignore
            Key={"id": id},
            UpdateExpression="set level_path=:level_path, config_name=:config_name, config_name_searchable=:config_name_searchable, description=:description, inherits=:inherits, active=:active, updated=:updated",
            ExpressionAttributeValues={
                ":level_path": path,
                ":config_name": name,
                ":config_name_searchable": name.lower(),
                ":description": description,
                ":inherits": 1 if inherits else 0,
                ":active": active,
                ":updated": time.time_ns()
            },            
            ReturnValues="ALL_NEW",
        )

        if response is None:
            return None

        dict = response["Attributes"]  # type: ignore

        if dict is None:
            return None

        return self.__config_item_from_dict(dict)        

    def set_current_by_id(self, id: str) -> ConfigItem:
    
        # first update the active stamp so it becomes the current
        current_config = self.activate_config_by_id(id)

        # TODO: in a thread?: 
        # find all others (others than the current, which is the latest active) and set active to 0 (to mark them as non active)
        self.__inactivate_non_current_configs(current_config.path, current_config.name, current_config.id)
        
        return current_config

    def set_non_current_by_id(self, id: str) -> ConfigItem:
    
        # first update the active stamp so it becomes inactive
        current_config = self.inactivate_config_by_id(id)
        
        return current_config

    def activate_config_by_id(self, id: str) -> ConfigItem:

        now_ns: int = time.time_ns()

        return self.__update_config_active_stamp(id, now_ns)

    def inactivate_config_by_id(self, id: str) -> ConfigItem:
        
        return self.__update_config_active_stamp(id, 0)

    def __update_config_active_stamp(self, id: str, active: int) -> ConfigItem:

        table = self.table_configs()

        now: int = active if active > 0 else time.time_ns() # assumes active is now when non-zero, so both timestamp match

        response = table.update_item(  # type: ignore
            Key={"id": id},
            UpdateExpression="set active=:active_stamp, updated=:updated",
            ExpressionAttributeValues={":active_stamp": active, ":updated": now},
            ReturnValues="ALL_NEW",
        )

        if response["Attributes"] is None:
            raise BaseException(f"Unable to update config item id {id}")

        retries_left: int = 2

        while (
                retries_left > 0
        ):  # deal with fetches not yet returning a successfully updated item

            config_item: Optional[ConfigItem] = self.get_config_by_id(id)

            if config_item is None or config_item.updated != now or config_item.active != active:
                log.warning(
                    f"Updated config but still not reflected. id: '{id}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return config_item
            
        raise BaseException(f"Unable to properly update config item id {id} after few attempts")

        # response: Dict[Any,Any] = response["Attributes"]

        # return self.__config_item_from_dict(response)

    def __inactivate_non_current_configs(self, level_path: str, config_name: str, current_id: str) -> bool:

        active_configs: Optional[List[ConfigItem]] = self.find_by_path_and_name(level_path, config_name)

        if active_configs is None:
            log.warning("Unable to determine active configs to inactivate")
            return False

        success: bool = True

        for c in active_configs:
            if c.active > 0 and c.id != current_id:
                try:
                    success = success and self.inactivate_config_by_id(c.id) is not None
                except Exception as e:
                    log.warning(f"Failed to inactivate config id {c.id}: {e}")
                    success = False

        return success    

    def get_config_by_id(self, id: str) -> Optional[ConfigItem]:

        dict = self.__get_config_item(id)

        if dict is None:
            return None

        return self.__config_item_from_dict(dict)

    def delete_config_by_id(self, id: str) -> Optional[ConfigItem]:

        table = self.table_configs()

        response = table.delete_item(
            Key={"id": id},
            ReturnValues="ALL_OLD",
        )

        dict = response.get("Attributes")

        return self.__config_item_from_dict(dict) if dict is not None else None

    def find_all(self, name: Optional[str], path: Optional[str], page_number: int, page_size: int, allowed_projects: Optional[List[str]]) -> Tuple[Optional[List[ConfigItem]], int]:
        
        name_substr: bool = False

        if name is not None and name.startswith("~"):            
            if len(name) == 1:
                name = None
            else:
                name = name[1:]
                name = name.lower()
                name_substr = True

        if name is not None and path is None:            
            if name_substr:
                filter_expression = "contains(config_name_searchable, :config_name)"
            else:
                filter_expression = "config_name = :config_name"
            attr_values={                
                ":config_name": { "S": name }
                }
        elif name is None and path is not None:
            filter_expression = "level_path = :level_path"
            attr_values={                
                ":level_path": { "S": path }
                }
        elif name is not None and path is not None:
            if name_substr:
                filter_expression = "contains(config_name_searchable, :config_name) and level_path = :level_path"
            else:
                filter_expression = "config_name = :config_name and level_path = :level_path"
            attr_values={                
                ":config_name": { "S": name },
                ":level_path": { "S": path }
                }
        else:
            filter_expression = ""
            attr_values = {}        

        try:
            if len(filter_expression) > 0:
                response = self.ddb_client().scan(
                    TableName=self.table_name(self.TABLE_CONFIGS_ALIAS),
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=attr_values, 
                    )
            else:
                response = self.ddb_client().scan(
                    TableName=self.table_name(self.TABLE_CONFIGS_ALIAS)                
                    )
        except Exception as e:
            log.error(e)
            return None, 0

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None:
            return None, 0

        if len(items) == 0:
            return [], 0
        
        unfiltered_configs = list(map(lambda i: self.__config_item_from_typed_dict(i), items))
        
        # filter out config items not visible to user due to lack of permissions
        filtered_configs: List[ConfigItem] = []

        if allowed_projects is None: 
            filtered_configs = unfiltered_configs # no filtering applied
        else:
            c: ConfigItem
            for c in unfiltered_configs:
                parsed_level = ParsedLevelPath.from_level_path(LevelPath.from_path(c.path))            
                if parsed_level is None:
                    continue # igfnore when unparseable - should not happen
                if parsed_level.show is not None: # is show is set then check permission
                    if parsed_level.show in allowed_projects:
                        filtered_configs.append(c)
                else:
                    filtered_configs.append(c)            

        if allowed_projects is not None:
            total_unfiltered_configs: int = len(unfiltered_configs)
            total_filtered_configs: int = len(filtered_configs)
            if total_unfiltered_configs > total_filtered_configs:
                log.debug(f"Excluding {total_unfiltered_configs - total_filtered_configs} config items after considered {len(allowed_projects)} allowed projects")
        else:
            log.warning(f"Projects are not being restricted. All matching projects are available")

        # order by name, then from upper to deeper path level (alphabetic order works in this case), finally by active and id
        filtered_configs.sort(key=lambda a: ( a.name, a.path, -a.active, a.id ), reverse=False)

        total: int = len(filtered_configs) 
        start_index, end_index = ApiUtils.page_selector(
            page_number, page_size, total
        )
                
        return filtered_configs[start_index:end_index], total


    def find_by_path(self, path: str) -> Optional[List[ConfigItem]]:

        canonized_path: str = LevelPath.canonize(path)

        try:
            response = self.ddb_client().query(
                TableName=self.table_name(self.TABLE_CONFIGS_ALIAS),
                IndexName=self.TABLE_CONFIGS_INDEX_PATH,
                KeyConditionExpression='level_path = :level_path',
                ExpressionAttributeValues={
                    ':level_path': {
                        'S': f"{canonized_path}"
                    }
                },
                ScanIndexForward=True)
        except Exception as e:
            log.error(e)
            return None

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None:
            return None

        if len(items) == 0:
            return []

        return list(map(lambda i: self.__config_item_from_typed_dict(i),
                        items))

    def find_by_path_and_name(self, path: str,
                              name: str) -> Optional[List[ConfigItem]]:

        canonized_path: str = LevelPath.canonize(path)

        try:
            response = self.ddb_client().query(
                TableName=self.table_name(self.TABLE_CONFIGS_ALIAS),
                IndexName=self.TABLE_CONFIGS_INDEX_PATH,
                KeyConditionExpression=
                'level_path = :level_path AND config_name = :config_name',
                ExpressionAttributeValues={
                    ':level_path': {
                        'S': f"{canonized_path}"
                    },
                    ':config_name': {
                        'S': f"{name}"
                    }
                },
                ScanIndexForward=True)
        except Exception as e:
            log.error(e)
            return None

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None:
            return None

        if len(items) == 0:
            return []

        return list(map(lambda i: self.__config_item_from_typed_dict(i),
                        items))

    def find_by_name(
            self,
            config_name: str,
            include_active_ones: bool = True,
            include_inactive_ones: bool = True) -> Optional[List[ConfigItem]]:

        key_condition_expression: str = 'config_name = :config_name'

        if not include_active_ones and not include_inactive_ones:
            return []

        if include_active_ones and not include_inactive_ones:
            key_condition_expression = f"{key_condition_expression} AND active > :active" # only actives
        elif not include_active_ones and include_inactive_ones:
            key_condition_expression = f"{key_condition_expression} AND active = :active" # only inactives
        else:
            key_condition_expression = f"{key_condition_expression} AND active >= :active" # both active and inactives

        exp_attr_values = {
            ':config_name': {
                'S': f"{config_name}"
            },
            ':active': {
                'N': '0'
            }
        }

        try:
            response = self.ddb_client().query(
                TableName=self.table_name(self.TABLE_CONFIGS_ALIAS),
                IndexName=self.TABLE_CONFIGS_INDEX_NAME,
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=exp_attr_values,
                ScanIndexForward=False)
        except Exception as e:
            log.error(e)
            return None

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None:
            return None

        if len(items) == 0:
            return []

        return list(map(lambda i: self.__config_item_from_typed_dict(i),
                        items))

    def find_active_ancestors_at_path_for_name(
            self, 
            level_path: str,
            config_name: str) -> Optional[List[ConfigItem]]:

        all_by_name: Optional[List[ConfigItem]] = self.find_by_name(
            config_name=config_name,
            include_active_ones=True,
            include_inactive_ones=False)

        if all_by_name is None:
            return None

        if len(all_by_name) == 0:
            return []

        level_path = f"{LevelPath.canonize(level_path)}/"

        # filter the ones that are actually ancestors of level_path
        ancestors = list(
            filter(lambda i: level_path.find(f"{i.path}/".replace("//", "/")) >= 0, all_by_name))            

        # order from upper to deeper level (alphabetic order works in this case)
        ancestors.sort(key=lambda a: a.path, reverse=False)

        # determine the current of active configs for each name/level (filter list)
        current_ancestors: List[ConfigItem] = []

        last_ancestor: Optional[ConfigItem] = None

        for a in ancestors:            
            if last_ancestor is not None and a.name == last_ancestor.name and a.path == last_ancestor.path:
                if last_ancestor.active > a.active:                        
                    continue # ignore iterated item if same name and level but older active timestamp
            current_ancestors.append(a)
            last_ancestor=a

        # now we have the list of ancestors filtered to remove items in same level+path to leave only the latest active (current)        
        return current_ancestors
        
    def find_inheritable_ancestors_at_path_for_name_in_bottom_up_order(
            self, 
            level_path: str,
            config_name: str) -> Optional[List[ConfigItem]]:

        current_ancestors = self.find_active_ancestors_at_path_for_name(level_path=level_path, config_name=config_name)

        if current_ancestors is None:
            return  None

        inheritables: List[ConfigItem] = []

        a: ConfigItem        
        for a in reversed(current_ancestors):
            inheritables.append(a)
            if not a.inherits:                
                break

        return inheritables
                
    def find_current_by_level_and_name(self, level_path: str, config_name: str) -> Optional[ConfigItem]:

        all_config_items: Optional[List[ConfigItem]] = self.find_by_name(config_name=config_name, include_active_ones=True, include_inactive_ones=False)

        if all_config_items is None:
            return None

        canonized_path: str = LevelPath.canonize(level_path)

        level_config_items: List[ConfigItem] = list( filter( lambda i: i.path == canonized_path, all_config_items) )

        if len(level_config_items) == 0:
            return None

        return level_config_items[0] # no need to sort: first one has largest "active" stamp because "active" is range-type key in index

    def __config_item_from_dict(self, config_item_dict: Any) -> ConfigItem:
        return ConfigItem(id=config_item_dict.get("id"),
                          path=config_item_dict.get("level_path"),
                          name=config_item_dict.get("config_name"),
                          description=config_item_dict.get("description"),
                          inherits=int(config_item_dict.get("inherits")) > 0,
                          created=int(config_item_dict.get("created")),
                          updated=int(config_item_dict.get("updated")),
                          created_by=config_item_dict.get("created_by"),
                          active=int(config_item_dict.get("active")))

    def __config_item_from_typed_dict(
            self, config_item_typed_dict: Any) -> ConfigItem:
        return ConfigItem(
            id=config_item_typed_dict.get("id").get('S'),
            path=config_item_typed_dict.get("level_path").get('S'),
            name=config_item_typed_dict.get("config_name").get('S'),            
            description=config_item_typed_dict.get("description").get('S'),
            inherits=int(config_item_typed_dict.get("inherits").get( 'N')) > 0,
            created=int(config_item_typed_dict.get("created").get('N')),
            updated=int(config_item_typed_dict.get("updated").get('N')),
            created_by=config_item_typed_dict.get("created_by").get('S'),
            active=int(config_item_typed_dict.get("active").get('N')))

    def __get_config_item(self, id: str) -> Optional[Any]:

        table = self.table_configs()

        response = table.get_item(Key={"id": id})

        dict: Optional[Any] = response.get("Item", None)

        return dict
