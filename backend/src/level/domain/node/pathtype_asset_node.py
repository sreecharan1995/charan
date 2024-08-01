from typing import List

from common.domain.path_type import PathType
from level.domain.node.asset_type_node import AssetTypeNode
from level.domain.node.base_node import BaseNode
from level.domain.tree_level import TreeLevel


class PathTypeAssetNode(BaseNode):
    """Represents the node of type asset in the internal tree
    """

    PATH_TYPE: PathType = PathType.ASSET

    _asset_types: List[AssetTypeNode]
    
    def __init__(self) -> None:                
        self._asset_types = []
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

        level.type = self.PATH_TYPE

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for at in self._asset_types:
            sub_levels.append(at.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._asset_types) > 0
        
    # overriden
    def _get_path_segment(self) -> str:

        return f"{self.PATH_TYPE.value}"

    def get_path_type(self) -> PathType:

        return self.PATH_TYPE
    
    def set_asset_types(self, asset_types: List[AssetTypeNode]):
        
        self._asset_types = asset_types

    def get_asset_types(self) -> List[AssetTypeNode]:

        return self._asset_types

    def asset_types_count(self) -> int:

        return len(self._asset_types)

    def assets_count(self) -> int:

        sum: int = 0

        for at in self._asset_types:
            sum = sum + at.assets_count()

        return sum
