from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from configs.domain.config_item import ConfigItem


class PatchConfigModel(BaseModel):    
    """Model to represents a request to patch (edit) a config attached to a level

    A config  level or name can be changed but only if its not currently active.
    """

    name: Optional[str] = Field(default=None,
                      title="the new name of config, if present",
                      example="config_default")

    level: Optional[LevelPathModel] = Field(
        default=None,
        title="an existing level path to re-attach the config to, if present")

    description: Optional[str] = Field(default=None, title="the new description of the config, if present", example="The default configuration")    

    inherits: Optional[bool] = Field(default=None, title="if this config inherits or not from parent configs", example=True)

    configuration: Optional[Dict[str,Any]] = Field(default=None,
                             title="the new configuration json, if present",
                             example={})
 
    @validator("name", always=True)
    def name_is_acceptable(cls, v: Optional[str]):
        if v is None:
            return v
        if not ConfigItem.is_name_valid(v):        
            raise ValueError("config name is invalid")
        return v

    @validator("level", always=True)
    def level_is_acceptable(cls, v: Optional[LevelPathModel]):
        
        if v is None:
            return v

        level_path: LevelPath = v.to_level_path()    
        if not ParsedLevelPath.is_path_acceptable(level_path.get_path()):
            raise ValueError("level is unparseable")
        return v

PatchConfigModel.update_forward_refs()
