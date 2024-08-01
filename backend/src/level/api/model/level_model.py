# coding: utf-8

from __future__ import annotations

from typing import List, Optional

from fastapi import Request
from pydantic import Field

from common.api.model.level_path_model import LevelPathModel
from common.api.utils import Utils as ApiUtils
from common.domain.path_type import PathType
from level.domain.tree_level import TreeLevel


class LevelModel(LevelPathModel):
    """Model to represent a level in the hierarchy of levels"""

    url: str = Field(default=None, title="the url of the level", example="")
    label: str = Field(
        default=None, title="a label for this level", example="nightshot4"
    )
    
    path: str = Field(default=None, title="the level path", example="/")    
    displayable_path: str = Field(default=None, title="the level path", example="/")    

    has_children: bool = Field(default=None, title="true when ", example="lookdown")
    children: Optional[List[LevelModel]] = Field(
        default=None, title="the sub-levels list", example="[]"
    )

    @staticmethod
    def from_tree_level(
        tree_level: TreeLevel, max_depth: int, req: Optional[Request] = None
    ) -> LevelModel:

        level_model: LevelModel = LevelModel()

        if tree_level.label is not None:
            level_model.label = tree_level.label

        if tree_level.division is not None:
            level_model.division = tree_level.division.value

        if tree_level.site is not None:
            level_model.site = tree_level.site.value

        if tree_level.path is None:
            level_model.path = "/"
        else:
            level_model.path = f"/{tree_level.path or ''}"

        if level_model.path != "/" and level_model.path.endswith("/"):
            level_model.path = level_model.path[:-1]

        if tree_level.project is not None:
            level_model.show = tree_level.project

        if tree_level.type is not None:

            if tree_level.type is PathType.ASSET:

                level_model.sequence_type = PathType.ASSET.value

                if tree_level.asset_type is not None:
                    level_model.sequence = tree_level.asset_type

                    if tree_level.asset_code is not None:
                        level_model.shot = tree_level.asset_code

            elif tree_level.type is PathType.SEQUENCE:

                level_model.sequence_type = PathType.SEQUENCE.value

                if tree_level.sequence_name is not None:
                    level_model.sequence = tree_level.sequence_name

                    if tree_level.shot_name is not None:
                        level_model.shot = tree_level.shot_name

        sublevels_count = len(tree_level.sublevels)

        if sublevels_count > 0:

            child_models: List[LevelModel] = []

            if max_depth > 0:
                for c in tree_level.sublevels:
                    child_models.append(
                        LevelModel.from_tree_level(c, max_depth - 1, req)
                    )
                level_model.children = child_models
            else:
                level_model.children = None

        level_model.has_children = tree_level.has_sublevels # do not depend on counting the included sublevels, but the reported fact

        level_model.displayable_path = level_model.path  # is the same

        if level_model.path is not None and req is not None:
            url_base = ApiUtils.base_url(req)
            level_model.url = f"{url_base}?path={level_model.path}"

        if level_model.label == "" and level_model.path == "/":
            level_model.label = "Root"

        return level_model


LevelModel.update_forward_refs()
