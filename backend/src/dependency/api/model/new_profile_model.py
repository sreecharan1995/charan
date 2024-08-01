# coding: utf-8

from __future__ import annotations

from typing import Optional

# from fastapi_permissions import Authenticated, Allow
from pydantic import BaseModel, Field, validator

from common.service.permissions_service import PermissionService
from dependency.domain.profile_item import ProfileItem

permission_service = PermissionService()


class NewProfileModel(BaseModel):
    """Model to represent a request to create a new profile
    """

    __actions__ = ["swds_create-profile"]

    name: str = Field(title="name of profile", description="The name to assign to the profile", example="Toronto 2")
    description: Optional[str] = Field(default="", title="profile description", description="An optional text describing the profile to be created", example="Toronto, new set")

    @validator("name", always=True)
    def name_is_acceptable(cls, v: str):
        if not ProfileItem.is_name_valid(v):
            raise ValueError("profile name is invalid")
        return v

    def __acl__(self): # type: ignore

        return permission_service.acls_for(NewProfileModel) # type: ignore


NewProfileModel.update_forward_refs()
