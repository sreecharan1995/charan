
from pydantic import BaseModel, Field


class ConfigStatusModel(BaseModel):
    """Model to represent a status for a config

    Internally configs can be active or inactive. The latest active is considered the current.
    """
    
    current: bool = Field(..., title="the status of the config", example=True)


ConfigStatusModel.update_forward_refs()
