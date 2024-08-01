# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from level.domain.node.root_node import RootNode


class TreeCountsModel(BaseModel):
    """Model to represent counts of objects contained in the hierarchy of levels.
    """
    
    projects: Optional[int] = Field(title="the number of projects", description="the ntotal number of projects (shows) contained in a tree", default=209)    
    assets: Optional[int] = Field(title="the number of assets", description="the total number of assets contained in a tree", default=3006)    
    asset_types: Optional[int] = Field(title="the number of asset types", description="the total number of asset types contained in a tree", default=30)    
    sequences: Optional[int] = Field(title="the number of sequences", description="the total number of sequences contained in a tree", default=717)    
    shots: Optional[int] = Field(title="the number of shots", description="the total number of shots contained in a tree", default=9170)    

    @staticmethod
    def from_tree_root(root_node: RootNode) -> TreeCountsModel:

        counts_model: TreeCountsModel = TreeCountsModel()

        counts_model.projects = root_node.projects_count()
        counts_model.assets = root_node.assets_count()
        counts_model.asset_types = root_node.asset_types_count()
        counts_model.sequences = root_node.sequences_count()
        counts_model.shots = root_node.shots_count()

        return counts_model

TreeCountsModel.update_forward_refs()
