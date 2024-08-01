from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from configs.domain.config_item import ConfigItem


class CreateConfigModel(BaseModel):
    """Model to represents a request to create a config attached to a level
    """

    name: str = Field(...,
                      title="name of config",
                      example="config_default")

    level: LevelPathModel = Field(...,
        title="an existing level path to attach the config to")

    description: Optional[str] = Field(default="",
                             title="the description of the config",
                             example="The default configuration")

    inherits: Optional[bool] = Field(default=True, title="if this configs inherits or not from its parent config", example=True)

    configuration: Dict[str,Any] = Field(...,
                             title="the configuration json",
                             example={})

    @validator("name", always=True)
    def name_is_acceptable(cls, v: str):        
        if not ConfigItem.is_name_valid(v):
            raise ValueError("config name is invalid")
        return v

    @validator("level", always=True)
    def level_is_acceptable(cls, v: LevelPathModel):        

        level_path: LevelPath = v.to_level_path()    
        if not ParsedLevelPath.is_path_acceptable(level_path.get_path()):
            raise ValueError("level is unparseable")
        return v    

CreateConfigModel.update_forward_refs()
