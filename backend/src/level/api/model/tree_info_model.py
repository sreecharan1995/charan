# coding: utf-8

from __future__ import annotations

from typing import Optional

from fastapi import Request
from pydantic import BaseModel, Field

from level.api.model.tree_counts_model import TreeCountsModel
from level.domain.tree import Tree


class TreeInfoModel(BaseModel):
    """Model to represent the status of a levels tree.

    This model is particularly used in the levels tree being serviced.
    """

    filename: Optional[str] = Field(title="the tree filename", description="the filename from where the tree was loaded", default=None, example="efc844b2e18b418aab6f453d26315403.sgtree")
    since: Optional[int] = Field(title="the time when the tree was loaded", description="the time when the tree was loaded and started being serviced, in seconds since epoch", default=None)
    uptime: Optional[int] = Field(title="the number of seconds since tree was loaded", description="the number of seconds since the tree was loaded and started being serviced", default=658)
    counts: Optional[TreeCountsModel] = Field(title="the tree objects count", description="the model representing tree objects counts", default=None)

    @staticmethod
    def from_tree(tree: Tree, req: Optional[Request] = None) -> TreeInfoModel:
        
        tree_info = TreeInfoModel()

        tree_info.filename = tree.get_filename()
        tree_info.since = tree.get_since(True)
        tree_info.uptime = tree.get_uptime(True)
        tree_info.counts = TreeCountsModel.from_tree_root(tree.get_root())

        return tree_info


TreeInfoModel.update_forward_refs()
