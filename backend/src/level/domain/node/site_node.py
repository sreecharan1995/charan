from typing import List

from common.domain.site import Site
from level.domain.node.base_node import BaseNode
from level.domain.node.division_node import DivisionNode
from level.domain.tree_level import TreeLevel


class SiteNode(BaseNode):
    """Represents a site node in the internal tree
    """

    _site: Site
    _divisions: List[DivisionNode]
    
    def __init__(self, site: Site) -> None:        
        self._site = site
        self._divisions = []
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

        level.site = self._site

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for d in self._divisions:
            sub_levels.append(d.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._divisions) > 0
        
    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._site.value}"

    def get_site(self) -> Site:

        return self._site    
    
    def set_divisions(self, divisions: List[DivisionNode]):
        
        self._divisions = divisions

    def get_divisions(self) -> List[DivisionNode]:

        return self._divisions

    def division_count(self) -> int:

        return len(self._divisions)
    
    def projects_count(self) -> int:
        sum: int = 0
        for d in self._divisions:
            sum = sum + d.projects_count()
        return sum

    def asset_types_count(self) -> int:
        sum: int = 0
        for d in self._divisions:
            sum = sum + d.asset_types_count()
        return sum

    def assets_count(self) -> int:
        sum: int = 0
        for d in self._divisions:
            sum = sum + d.assets_count()
        return sum

    def sequences_count(self) -> int:
        sum: int = 0
        for p in self._divisions:
            sum = sum + p.sequences_count()
        return sum

    def shots_count(self) -> int:
        sum: int = 0
        for p in self._divisions:
            sum = sum + p.shots_count()
        return sum