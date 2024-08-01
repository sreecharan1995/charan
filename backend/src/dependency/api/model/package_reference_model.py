# coding: utf-8

from __future__ import annotations

import re
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field, validator


class PackageReferenceModel(BaseModel):
    """Model to represent a package reference.

    A package reference consist of a package name and a reference to one of the existing versions of the package.
    """

    name: Optional[str] = Field(title="the name of the package", description="The name identifying the package", default=None, example="ocio")
    version: Optional[str] = Field(title="the version of the package", description="The specific version of the package", default=None, version="1.0.9")
    #  url: Optional[str] = Field(title="the url of the package", description="The specific version of the package", default=None)
    use_legacy: Optional[bool] = Field(default=False, title="Legacy flag", description="It will determines the package version is legacy or not", example="true")

    def is_deleted(self) -> bool:
        return self.version == "!"

    def mark_deleted(self):
        self.version = "!"

    @validator("name", always=True)
    def name_is_acceptable(cls, v: str):
        if v is None:
            raise HTTPException(status_code=422, detail="package name is missing")
        pattern = "^[a-zA-Z0-9][-\\w]{1,64}$"
        if not re.match(pattern, v):
            raise HTTPException(
                status_code=422, detail=f"package name '{v}' does not match pattern " + pattern
            )
        return v

    @validator("version")
    def version_is_acceptable(cls, v: str):
        if type(v) != str:
            raise HTTPException(
                status_code=422, detail="package version is not a string"
            )
        if v.strip() == '':
            raise HTTPException(
                status_code=422, detail="package version is empty"
            )
        # pattern = "^([-\\w\\.]{1,64})$"
        # if not re.match(pattern, v) and not v == "!":
        #     raise HTTPException(
        #         status_code=422,
        #         detail=f"package version '{v}' does not match pattern "
        #         + pattern,
        #     )
        return v


PackageReferenceModel.update_forward_refs()
