# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator


class PatchProfileModel(BaseModel):
    """Model to represent a request to change (patch) some of the properties of a profile.
    """

    name: Optional[str] = Field(default=None, title="profile name", description="The new name for the profile", example="Show 456 profile")
    description: Optional[str] = Field(default=None, title="profile description", description="The new description for the profile", example="This versions are specific for show 456")
    path: Optional[str] = Field(default=None, title="profile level path", description="The path for the new level of the (new) profile", example="/mumbai/Project1/Show456")

    @validator("name", always=True)
    def name_is_acceptable(cls, v: str):
        if v is not None and v.strip() == "":
            raise ValueError("profile name is invalid")
        return v


PatchProfileModel.update_forward_refs()
