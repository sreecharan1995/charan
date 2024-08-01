# coding: utf-8

from __future__ import annotations

from typing import List

from pydantic import Field, validator

from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.api.model.profile_comment_model import ProfileCommentModel
from dependency.api.model.profile_model import ProfileModel


class FullProfileModel(ProfileModel):
    """Model to represent a profile, effective at a level of the levels hierarchy. 
    
    A profile includes packages, bundles, comments and other level-related properties.        
    """
    ...
    packages: List[PackageReferenceModel] = Field(default=[], title="list of packages", description="The package references in the effective profile at this level", example=[])
    bundles: List[BundleModel] = Field(default=[], title="list of bundles", description="The list of bundles in the effective profile at this level", example=[])
    comments: List[ProfileCommentModel] = Field(default=[], title="comments list", description="The profile comments list") # TBI: remove comments from here, from effective profiles

    @validator("name", always=True)
    def name_is_acceptable(cls, v : str):                
        if v.strip() == '':
            raise ValueError("profile name is invalid")
        return v

FullProfileModel.update_forward_refs()