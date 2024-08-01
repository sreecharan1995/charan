import copy
from typing import List

from common.domain.site import Site
from level.domain.node.base_node import BaseNode
from level.domain.node.division_node import DivisionNode
from level.domain.node.site_node import SiteNode
from level.domain.tree_level import TreeLevel


class RootNode(BaseNode):
    """Represents the root node in the internal tree
    """

    _sites: List[SiteNode]
    _divisions: List[
        DivisionNode
    ] = []  # keep the divisions list also (is the one being gets serialized)

    def __init__(self, divisions: List[DivisionNode]) -> None:
        self._divisions = divisions
        return

    # overriden
    def _get_path_segment(self) -> str:
        return ""

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []

        for s in self._sites:
            sub_levels.append(s.as_level(max_depth))

        return sub_levels

    # overriden
    def _has_sublevels(self) -> bool:
        return len(self._sites) > 0

    def get_sites(self) -> List[SiteNode]:

        return self._sites

    def site_count(self) -> int:

        return len(self._sites)

    def divisions_count(self, per_site: bool = True) -> int:
        if per_site:
            return len(self._divisions)
        else:
            sum: int = 0
            for s in self._sites:
                sum = sum + s.division_count()
            return sum

    def projects_count(self, per_site: bool = True) -> int:
        sum: int = 0
        if per_site:
            for d in self._divisions:
                sum = sum + d.projects_count()
        else:
            for s in self._sites:
                sum = sum + s.projects_count()
        return sum

    def asset_types_count(self, per_site: bool = True) -> int:
        sum: int = 0
        if per_site:
            for d in self._divisions:
                sum = sum + d.asset_types_count()
        else:
            for s in self._sites:
                sum = sum + s.asset_types_count()
        return sum

    def assets_count(self, per_site: bool = True) -> int:
        sum: int = 0
        if per_site:
            for d in self._divisions:
                sum = sum + d.assets_count()
        else:
            for s in self._sites:
                sum = sum + s.assets_count()
        return sum

    def sequences_count(self, per_site: bool = True) -> int:
        sum: int = 0
        if per_site:
            for d in self._divisions:
                sum = sum + d.sequences_count()
        else:
            for s in self._sites:
                sum = sum + s.sequences_count()
        return sum

    def shots_count(self, per_site: bool = True) -> int:
        sum: int = 0
        if per_site:
            for d in self._divisions:
                sum = sum + d.shots_count()
        else:
            for s in self._sites:
                sum = sum + s.shots_count()
        return sum

    def prepare_for_service(self):

        self._parent = None

        for d in self._divisions:

            d.set_parent(self)

            for p in d.get_projects():

                p.set_parent(d)

                pathtype_asset = p.get_pathtype_asset()
                for at in pathtype_asset.get_asset_types():
                    at.set_parent(pathtype_asset)

                    for a in at.get_assets():
                        a.set_parent(at)

                pathtype_asset.set_parent(p)

                pathtype_sequence = p.get_pathtype_sequence()
                for s in pathtype_sequence.get_sequences():
                    s.set_parent(pathtype_sequence)

                    for t in s.get_shots():
                        t.set_parent(s)

                pathtype_sequence.set_parent(p)

        # assign a prepared divisions copy to each site node:

        site_nodes: List[SiteNode] = []

        for s in Site:

            divisions_copy: List[DivisionNode] = copy.deepcopy(
                self._divisions
            )  # TODO: improve in the future to save memory
            site_node: SiteNode = SiteNode(s)

            for d in divisions_copy:
                d.set_parent(site_node)

            site_node.set_divisions(divisions_copy)

            site_node.set_parent(self)  # set the parent on each site node
            site_nodes.append(site_node)

        self._sites = site_nodes
