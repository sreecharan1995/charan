# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator

PROFILE_STATUS_PENDING: str = "pending"
PROFILE_STATUS_VALID: str = "valid"
PROFILE_STATUS_INVALID: str = "invalid"


class ProfileModel(BaseModel):
    """Model to represent a profile.

    A profile is a both a package and a bundle set attached to a level of the levels tree."""

    id: str = Field(
        default="",
        title="profile id",
        description="The unique id for the profile",
        example="profile_jekpqwrs",
    )
    path: str = Field(
        default="",
        title="level path",
        description="The path notation for this profile level",
        example="/mumbai",
    )
    displayable_path: str = Field(
        default="/",
        title="displayable level path",
        description="The project-friendly path notation for the profile level",
        example="/mumbai/Project/a3d",
    )
    name: str = Field(
        default="",
        title="name of the profile",
        description="The name for the profile",
        example="Mumbai variants",
    )
    description: Optional[str] = Field(
        default=None,
        title="description of profile",
        description="The optional text describing the profile",
        example="All version variants to be used under Mumbai site",
    )
    created_at: str = Field(
        default="",
        title="date of creation",
        description="The timestamp of profile creation",
        example="2022-Jul-06T17:32:57",
    )
    created_by: str = Field(
        default="",
        title="name of creator",
        description="The name of the creator",
        example="system",
    )
    profile_status: str = Field(
        title="profile validation status",
        description="The validation status for this profile",
        default=PROFILE_STATUS_PENDING,
    )

    @validator("name", always=True)
    def name_is_acceptable(cls, v: str):
        if v.strip() == "":
            raise ValueError("profile name is invalid")
        return v


ProfileModel.update_forward_refs()
