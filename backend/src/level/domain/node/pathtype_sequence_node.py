from typing import List

from common.domain.path_type import PathType
from level.domain.node.base_node import BaseNode
from level.domain.node.sequence_node import SequenceNode
from level.domain.tree_level import TreeLevel


class PathTypeSequenceNode(BaseNode):
    """Represents the node of type sequence in the internal tree
    """

    PATH_TYPE: PathType = PathType.SEQUENCE

    _sequences: List[SequenceNode]
    
    def __init__(self) -> None:                
        self._sequences = []
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

        level.type = self.PATH_TYPE

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for a in self._sequences:
            sub_levels.append(a.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._sequences) > 0
        
    # overriden
    def _get_path_segment(self) -> str:

        return f"{self.PATH_TYPE.value}"

    def get_path_type(self) -> PathType:

        return self.PATH_TYPE
    
    def set_sequences(self, sequences: List[SequenceNode]):
        
        self._sequences = sequences

    def get_sequences(self) -> List[SequenceNode]:

        return self._sequences

    def sequences_count(self) -> int:

        return len(self._sequences)            

    def shots_count(self) -> int:

        sum: int = 0
        for s in self._sequences:
            sum = sum + s.shots_count()        
        return sum
