# coding: utf-8

from __future__ import annotations

from pydantic import BaseModel, Field


class SiteModel(BaseModel):
    """Model to represent one of the sites.
    
    A site is a location where profiles resources are attached to a tree-like hierarchy of logical levels. A site
    is a inmediate sublevel of the root level.
    """

    id: str = Field(
        default=None,
        title="the site id",
        description="The unique, unmodifiable identifier of the site",
        example="mumbai"
    )
    name: str = Field(
        default=None,
        title="the site name",
        description="The name of the site, as used when shown on screen",
        example="Mumbai"
    )

SiteModel.update_forward_refs()
