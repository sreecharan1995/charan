# coding: utf-8

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field, validator

from dependency.api.model.package_reference_model import PackageReferenceModel


class BundleModel(BaseModel):
    """Model to represent a bundle.
    
    A bundle is a list of package references. It is identified by a name, and may have description.
    """

    name: str = Field(title="name of bundle", description="The name identifying the bundle", example="maya_dev")
    description: str = Field(default="", title="description of bundle", description="The optional description for the bundle", example="standard packages for maya development")
    packages: List[PackageReferenceModel] = Field(title="packages list", description="The list of package references included the bundle", default=[], example=[ { "name": "ocio", "version": "1.0.9" }, { "name": "numpy", "version": "1.16.0" } ])

    def is_empty(self) -> bool:
        return len(self.packages) == 0
        
    @validator("name", always=True)
    def name_is_acceptable(cls, v : str):
        if v is None:
            raise ValueError("bundle name is missing")
        pattern = "^[a-zA-Z0-9][-\\w]{1,64}$"
        if not re.match(pattern, v):
            raise ValueError("bundle name does not match pattern " + pattern)
        return v

    def packages_match(self, pk_list : List[PackageReferenceModel]) -> bool:
        if len(self.packages) == 0 or len(pk_list) == 0:            
            return False

        if len(self.packages) != len(pk_list):
            return False

        for i in range(0, len(self.packages)):
            sp = self.packages[i]
            op = pk_list[i]
            if sp.name != op.name or sp.version != op.version:
                return False

        return True        

BundleModel.update_forward_refs()

