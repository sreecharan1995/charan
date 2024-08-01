from typing import Optional
from common.domain.sg.shotgrid_asset import ShotgridAsset

from common.logger import log
from level.domain.node.base_node import BaseNode
from level.domain.tree_level import TreeLevel


class AssetNode(BaseNode):
    """Represents an asset node in the internal tree
    """

    _id: int
    _code: str
    _type: str

    def __init__(self, id: int, code: str, type: str) -> None:
        self._id = id
        self._code = code
        self._type = type
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)                

        level.asset_code = self._code

    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._code}"


    def get_id(self) -> int:

        return self._id

    def get_code(self) -> str:

        return self._code

    def get_type(self) -> str:

        return self._type
    
    @staticmethod
    def asset_from_sg(sg_asset: ShotgridAsset) -> Optional['AssetNode']:

        asset_id: Optional[int] = sg_asset.get_id()

        if asset_id is None or asset_id <= 0:
            log.warning(f"Unable to create asset: asset id '{asset_id if asset_id is not None else ''}': missing or unusable")
            return None

        asset_code: Optional[str] = sg_asset.get_code()

        if  asset_code is None or len(asset_code.strip()) == 0:
            log.warning(
                f"Unable to create asset: asset code '{asset_code or ''}': missing or unusable"
            )
            return None

        asset_type: Optional[str] = sg_asset.get_type()

        if asset_type is None or len(asset_type.strip()) == 0:
            log.warning(
                f"Unable to create asset: asset type '{asset_type or ''}': missing or unusable"
            )
            return None

        return AssetNode(asset_id, asset_code.strip(), asset_type.strip())
