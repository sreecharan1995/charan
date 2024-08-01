
from typing import Any, Dict

from pydantic import Field

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.utils import Utils
from configs.api.model.compact_config_model import CompactConfigModel
from configs.domain.config_item import ConfigItem


class ConfigModel(CompactConfigModel):
    """Model to represent a config attached to a level
    """       

    configuration: Dict[str,Any] = Field(
        default=None, title="configuration json", example={}
    )

    @staticmethod
    def from_config_item_and_json(config_item: ConfigItem, config_json: Dict[str,Any]) -> 'ConfigModel':

        return ConfigModel(
            id=config_item.id,
            name=config_item.name, 
            path=config_item.path,
            level=LevelPathModel.from_level_path(LevelPath(config_item.path)),
            description=config_item.description, 
            inherits=config_item.inherits,
            current=config_item.active is not None and config_item.active > 0,
            created=Utils.get_date_time(config_item.created),
            updated=Utils.get_date_time(config_item.updated),
            configuration=config_json,
            created_by=config_item.created_by)


ConfigModel.update_forward_refs()
