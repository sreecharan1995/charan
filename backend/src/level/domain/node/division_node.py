from typing import List

from common.domain.division import Division
from level.domain.node.base_node import BaseNode
from level.domain.node.project_node import ProjectNode
from level.domain.tree_level import TreeLevel


class DivisionNode(BaseNode):
    """Represents a division node in the internal tree
    """

    _division: Division
    _projects: List[ProjectNode]

    def __init__(self, division: Division) -> None:
        self._division = division
        self._projects = []
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

        level.division = self._division

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for p in self._projects:
            sub_levels.append(p.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._projects) > 0

    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._division.value}"

    def get_division(self) -> Division:

        return self._division

    def set_projects(self, projects: List[ProjectNode]):

        self._projects = projects

    def get_projects(self) -> List[ProjectNode]:

        return self._projects

    def projects_count(self) -> int:

        return len(self._projects)

    def asset_types_count(self) -> int:
        sum: int = 0
        for p in self._projects:
            sum = sum + p.asset_types_count()
        return sum

    def assets_count(self) -> int:
        sum: int = 0
        for p in self._projects:
            sum = sum + p.assets_count()
        return sum

    def sequences_count(self) -> int:
        sum: int = 0
        for p in self._projects:
            sum = sum + p.sequences_count()
        return sum

    def shots_count(self) -> int:
        sum: int = 0
        for p in self._projects:
            sum = sum + p.shots_count()
        return sum
