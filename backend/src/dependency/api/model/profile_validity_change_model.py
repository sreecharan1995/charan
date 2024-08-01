# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator


class ProfileValidityChangeModel(BaseModel):
    """Model representing a validity status change for a profile
    """

    id: str = Field(default="", title='id of profile', description='The id of the profile for which the validation status is changing', example="profile_fdstsd")
    validation_result: str =  Field(default="", title='validation status', description='The valid or invalid value for the status', example="invalid")
    result_reason: Optional[str] = Field(default="", title='result reason', description='The message with some details about the result')
    rxt: Optional[str] = Field(default="", title='path to rxt', description='The path to the produced rxt file, if produced')

    @validator("validation_result", always=True)
    def validation_result_is_acceptable(cls, v: str):
        if v is not None and (v.lower() == "valid" or v.lower() == "invalid"):
            return v

        raise ValueError("validation_result must be 'valid' or 'invalid'")


ProfileValidityChangeModel.update_forward_refs()


class ProfileValidityEvent(BaseModel):

    """ProfileValidityEvent - a model describing the payload for the event incoming holding details with validity changes for a profile"""

    detail_type: str = Field(alias="detail-type")
    detail: ProfileValidityChangeModel

    @validator("detail_type", always=True)
    def detail_type_is_acceptable(cls, v: str):
        if v is not None and v == "profile-validation-completed":
            return v

        raise ValueError("detail-type must be 'profile-validation-completed'")


ProfileValidityEvent.update_forward_refs()
