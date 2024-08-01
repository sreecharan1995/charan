from typing import List

from level.domain.node.asset_node import AssetNode
from level.domain.node.base_node import BaseNode
from level.domain.tree_level import TreeLevel


class AssetTypeNode(BaseNode):
    """Represents an asset-type node in the internal tree
    """

    _asset_type: str
    _assets: List[AssetNode]
    
    def __init__(self) -> None:                
        self._assets = []
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

        level.asset_type = self._asset_type

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for a in self._assets:
            sub_levels.append(a.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._assets) > 0
                
    # overriden
    def _get_path_segment(self) -> str:

        return f"{self._asset_type}"

    def set_asset_type(self, asset_type: str):

        self._asset_type = asset_type

    def get_asset_type(self) -> str:

        return self._asset_type

    def add_asset(self, asset: AssetNode):

        self._assets.append(asset)

    def set_assets(self, assets: List[AssetNode]):
        
        self._assets = assets

    def get_assets(self) -> List[AssetNode]:

        return self._assets

    def assets_count(self) -> int:

        return len(self._assets)            
