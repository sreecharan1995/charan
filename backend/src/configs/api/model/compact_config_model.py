
from typing import Optional

from pydantic import BaseModel, Field

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.utils import Utils
from configs.domain.config_item import ConfigItem


class CompactConfigModel(BaseModel):
    """Model to represent a config attached to a level, excluding the json data

    Some properties are not included compared to the ConfigModel model
    """
    
    id: str = Field(
        default=None, title="id config", example="djdhdvf7dsnjdskdshsd8dsfdsf89dfd999323"
    )

    name: str = Field(
        default=None, title="name of config", example="config_default"
    )    

    path: str = Field(default=None, title="the level path", example="/")    

    level: LevelPathModel = Field(default=None, title="the level", example={})

    description: str = Field(
        default=None, title="the description of the config", example="The default configuration"
    )

    current: Optional[bool] = Field(default=None,
        title="active or inactive status", example=True
    )    

    inherits: bool = Field(default=None, title="if this config inherits from its parent config or not", example=True)
    
    created: str = Field(
        title="the creation time stamp"
    )

    created_by: str = Field(
        title="the user that created the config"
    )

    updated: str = Field(
        title="the last-updated time stamp"
    )

    @staticmethod
    def from_config_item(config_item: ConfigItem) -> 'CompactConfigModel':

        return CompactConfigModel(
            id=config_item.id,
            name=config_item.name, 
            path=config_item.path,
            level=LevelPathModel.from_level_path(LevelPath(config_item.path)),
            description=config_item.description, 
            current=config_item.active is not None and config_item.active > 0,
            inherits=config_item.inherits,
            created=Utils.get_date_time(config_item.created),
            updated=Utils.get_date_time(config_item.updated),
            created_by=config_item.created_by)


CompactConfigModel.update_forward_refs()
