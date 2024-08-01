from typing import Optional
from common.domain.sg.shotgrid_shot import ShotgridShot

from common.logger import log
from level.domain.node.base_node import BaseNode
from level.domain.tree_level import TreeLevel


class ShotNode(BaseNode):
    """Represents a shot node in the internal tree
    """

    _id: int
    _name: str

    def __init__(self, id: int, name: str) -> None:
        self._id = id
        self._name = name
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)                

        level.shot_name = self._name

    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._name}"

    def get_id(self) -> int:

        return self._id

    def get_name(self) -> str:

        return self._name

    @staticmethod
    def shot_from_sg(sg_shot: ShotgridShot) -> Optional['ShotNode']:

        shot_id: Optional[int] = sg_shot.get_id()

        if shot_id is None or shot_id <= 0:
            log.warning(f"Unable to create shot: shot id '{shot_id if shot_id is not None else ''}': missing or unusable")
            return None

        shot_name: Optional[str] = sg_shot.get_name()

        if shot_name is None or len(shot_name.strip()) == 0:
            log.warning(
                f"Unable to create shot: shot name '{shot_name or ''}': missing or unusable"
            )
            return None

        return ShotNode(shot_id, shot_name.strip())