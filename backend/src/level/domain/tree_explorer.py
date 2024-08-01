from typing import Optional

from common.domain.division import Division
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.path_type import PathType
from common.domain.site import Site
from level.domain.node.asset_node import AssetNode
from level.domain.node.asset_type_node import AssetTypeNode
from level.domain.node.base_node import BaseNode
from level.domain.node.division_node import DivisionNode
from level.domain.node.pathtype_asset_node import PathTypeAssetNode
from level.domain.node.pathtype_sequence_node import PathTypeSequenceNode
from level.domain.node.project_node import ProjectNode
from level.domain.node.root_node import RootNode
from level.domain.node.sequence_node import SequenceNode
from level.domain.node.shot_node import ShotNode
from level.domain.node.site_node import SiteNode
from level.domain.tree import Tree


class TreeExplorer():
    """Provides the methods to find or list nodes present in the internal tree representation of project assets and sequences
    """

    __root_node: RootNode

    def __init__(self, tree: Tree):
        self.__root_node = tree.get_root()

    def find_node_by_path(self, parsed_path: ParsedLevelPath) -> Optional[BaseNode]:
        
        if parsed_path.site is None:
            return self.__root_node

        site_node: Optional[SiteNode] = self.find_site(parsed_path.site)

        if site_node is None:
            return None # site not found - in practice all sites has content, the same content, so it should not happen
                
        if parsed_path.division is None:
            return site_node

        division_node: Optional[DivisionNode] = self.find_division(site_node, parsed_path.division)

        if division_node is None:            
            return None # division not found

        if parsed_path.show is None:
            return division_node # return division node, ignore other more specific fields

        project_node: Optional[ProjectNode] = self.find_project(division_node, parsed_path.show)

        if project_node is None:
            return None # not found in division

        if project_node.get_division() != parsed_path.division:
            return None # force not found after finding inconsistency - should not happen

        if parsed_path.type is None:
            return project_node # return project, ignore other more specific fields

        if parsed_path.type == PathType.ASSET:

            pathtype_asset_node: PathTypeAssetNode = project_node.get_pathtype_asset()

            if parsed_path.asset_type is None:
                return pathtype_asset_node

            asset_type_node: Optional[AssetTypeNode] = self.find_asset_type(pathtype_asset_node, parsed_path.asset_type)

            if asset_type_node is None:
                return None
            
            if parsed_path.asset_code is None:
                return asset_type_node

            asset_node: Optional[AssetNode] = self.find_asset(asset_type_node, parsed_path.asset_code)    

            if asset_node is None:
                return None

            return asset_node

        elif parsed_path.type == PathType.SEQUENCE:

            pathtype_sequence_node: PathTypeSequenceNode = project_node.get_pathtype_sequence()
            
            if parsed_path.sequence_name is None:
                return pathtype_sequence_node

            sequence_node: Optional[SequenceNode] = self.find_project_sequence(pathtype_sequence_node, parsed_path.sequence_name)

            if sequence_node is None:
                return None
            
            if parsed_path.shot_name is None:
                return sequence_node

            shot_node: Optional[ShotNode] = self.find_project_sequence_shot(sequence_node, parsed_path.shot_name)    

            if shot_node is None:
                return None

            return shot_node        

        return None # assume not found

    def find_site(self, site: Site) -> Optional[SiteNode]:

        for s in self.__root_node.get_sites():
            if s.get_site() == site:
                return s

        return None

    def find_division(self, site_node: SiteNode, division: Division) -> Optional[DivisionNode]:

        for d in site_node.get_divisions():
            if d.get_division() == division:
                return d

        return None

    def find_project(self, division_node: DivisionNode, project_name: str) -> Optional[ProjectNode]:

        for p in division_node.get_projects():
            if p.get_name() == project_name:
                if division_node.get_division() != p.get_division():
                    return None # inconsistency: not in same division -- should not happen
                return p

        return None

    def find_asset_type(self, pathtype_asset_node: PathTypeAssetNode, asset_type: str) -> Optional[AssetTypeNode]:

        for a in pathtype_asset_node.get_asset_types():
            if a.get_asset_type() == asset_type:
                return a

        return None

    def find_asset(self, asset_type_node: AssetTypeNode, asset_code: str) -> Optional[AssetNode]:

        for a in asset_type_node.get_assets():
            if a.get_code() == asset_code:
                return a

        return None

    def find_project_sequence(self, sequence_type_node: PathTypeSequenceNode, sequence_name: str) -> Optional[SequenceNode]:

        for s in sequence_type_node.get_sequences():
            if s.get_code() == sequence_name:  # internally is 'code'
                return s

        return None

    def find_project_sequence_shot(self, sequence_node: SequenceNode, shot_name: str) -> Optional[ShotNode]:
        
        for t in sequence_node.get_shots():
            if t.get_name() == shot_name:
                return t

        return None
