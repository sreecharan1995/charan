from typing import List, Optional
from common.domain.sg.shotgrid_sequence import ShotgridSequence
from common.domain.sg.shotgrid_shot import ShotgridShot

from common.logger import log
from level.domain.node.base_node import BaseNode
from level.domain.node.shot_node import ShotNode
from level.domain.tree_level import TreeLevel


class SequenceNode(BaseNode):
    """Represents a sequence node in the internal tree
    """

    _id: int
    _code: str
    _shots: List[ShotNode] = []

    def __init__(self, id: int, code: str) -> None:
        self._id = id
        self._code = code
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)                

        level.sequence_name = self._code # internally is a 'code' field attr

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for t in self._shots:
            sub_levels.append(t.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._shots) > 0

    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._code}"

    def get_id(self) -> int:

        return self._id

    def get_code(self) -> str:

        return self._code

    def get_shots(self) -> List[ShotNode]:

        return self._shots    

    def set_shots(self, shots: List[ShotNode]):
        self._shots = shots

    def shots_count(self) -> int:

        return len(self._shots)

    @staticmethod
    def sequence_from_sg(sg_sequence: ShotgridSequence) -> Optional["SequenceNode"]:

        sequence_id: Optional[int] = sg_sequence.get_id()

        if sequence_id is None or sequence_id <= 0:
            log.warning(f"Unable to create sequence: sequence id '{sequence_id if sequence_id is not None else ''}': missing or unusable")
            return None

        sequence_code: Optional[str] = sg_sequence.get_code()

        if sequence_code is None or len(sequence_code.strip()) == 0:
            log.warning(
                f"Unable to create sequence: sequence code '{sequence_code or ''}': missing or unusable"
            )
            return None

        sg_sequence_shots: List[ShotgridShot] = sg_sequence.get_shots() or []

        shots: List[ShotNode] = []

        sequence = SequenceNode(sequence_id, sequence_code.strip())

        for ss in sg_sequence_shots:
            shot: Optional[ShotNode] = ShotNode.shot_from_sg(ss)
            if shot is None:
                log.warning(f"Unable to create sequence shot from: {ss.__dict__}")
                continue
            shots.append(shot)

        sequence.set_shots(shots)

        return sequence
        
