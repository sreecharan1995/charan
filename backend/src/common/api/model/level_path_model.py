# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.path_type import PathType


class LevelPathModel(BaseModel):
    """Represents a level reference (a path in json format)"""

    site: str = Field(default=None, title="the site of the level", example="Mumbai")

    division: str = Field(
        default=None, title="the division of the level", example="television"
    )

    show: str = Field(default=None, title="the show of the level", example="lookdown")

    sequence_type: str = Field(
        default=None, title="if it is an asset or a sequence type", example="asset"
    )  # TODO: this is a bad name: assets are not sequences, right?

    sequence: str = Field(
        default=None,
        title="if it is an asset, this is the asset type, if a sequence then it is a sequence name",
        example="vehicle",
    )  # TODO: this is a bad name: assets are not sequences, right?

    shot: str = Field(
        default=None,
        title="if it is an asset, this is the asset code, but if a sequence it is a shot name ",
        example="345",
    )  # TODO: this is a bad name: assets are not sequences, right?

    def to_level_path(self) -> LevelPath:
        return LevelPath(path=f"/{self.site or ''}/{self.division or ''}/{self.show or ''}/{self.sequence_type or ''}/{self.sequence or ''}/{self.shot or ''}")

    @staticmethod
    def from_level_path(level_path: LevelPath) -> 'LevelPathModel':
                            
        model: LevelPathModel = LevelPathModel()        

        parsed_level_path: Optional[ParsedLevelPath] = ParsedLevelPath.from_level_path(level_path)

        if parsed_level_path is None:
            raise Exception(f"Unable to parse: {level_path.get_path()}")

        if parsed_level_path.site is None:
            return model

        model.site = parsed_level_path.site.value

        if parsed_level_path.division is None:
            return model

        model.division = parsed_level_path.division.value

        if parsed_level_path.show is None:
            return model

        model.show = parsed_level_path.show

        if parsed_level_path.type is None:
            return model

        model.sequence_type = parsed_level_path.type.value

        if parsed_level_path.type == PathType.SEQUENCE:
            
            if parsed_level_path.sequence_name is None:
                return model

            model.sequence = parsed_level_path.sequence_name

            if parsed_level_path.shot_name is None:
                return model

            model.shot = parsed_level_path.shot_name

        elif parsed_level_path.type == PathType.ASSET:

            if parsed_level_path.asset_type is None:
                return model

            model.sequence = parsed_level_path.asset_type

            if parsed_level_path.asset_code is None:
                return model

            model.shot = parsed_level_path.asset_code

        return model

LevelPathModel.update_forward_refs()
