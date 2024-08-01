# coding: utf-8

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class PackageModel(BaseModel):
    """Model to represent an existing specific package.
    
    A package represents an installable product. It has a name, and a set of available versions.
    """

    name: str = Field(default=None, title="name of package", description="The name of the package", example="katana")
    category: str = Field(default=None, title="category of package", description="The category of the package.", example="python_pkgs")
    path: str = Field(default=None, title="path of the package", description="The disk path where the package is located", example="/mount/spin-rez/spin-rez/rez/python_pkgs/katana")
    versions: List[str] = Field(default=None, title="list of versions", description="The list of available versions of the package", example=["3.6v1","3.6v2"])

PackageModel.update_forward_refs()
