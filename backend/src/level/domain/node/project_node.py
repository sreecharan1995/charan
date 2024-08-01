from typing import List, Optional

from common.domain.division import Division
from common.domain.sg.shotgrid_project import ShotgridProject
from common.logger import log
from level.domain.node.base_node import BaseNode
from level.domain.node.pathtype_asset_node import PathTypeAssetNode
from level.domain.node.pathtype_sequence_node import PathTypeSequenceNode
from level.domain.tree_level import TreeLevel


class ProjectNode(BaseNode):
    """Represents a project node in the internal tree
    """

    _id: int
    _division: Division
    _name: str
    _type_assets: PathTypeAssetNode
    _type_sequences: PathTypeSequenceNode

    def __init__(self, division: Division, id: int, name: str) -> None:
        self._division = division
        self._id = id
        self._name = name
        self._type_assets = PathTypeAssetNode()
        self._type_sequences = PathTypeSequenceNode()
        return

    # overriden
    def _fill_level(self, level: TreeLevel):

        super()._fill_level(level)                

        level.project = self._name

    # overriden
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:

        sub_levels: List[TreeLevel] = []
     
        sub_levels.append(self._type_assets.as_level(max_depth))
        sub_levels.append(self._type_sequences.as_level(max_depth))

        return sub_levels
        
    # overriden
    def _has_sublevels(self) -> bool:
        return True

    # overriden
    def _get_path_segment(self) -> str:
        return f"{self._name}"

    def get_division(self) -> Division:

        return self._division

    def get_id(self) -> int:

        return self._id

    def get_name(self) -> str:

        return self._name    

    def assets_count(self) -> int:

        return self._type_assets.assets_count()

    def asset_types_count(self) -> int:

        return self._type_assets.asset_types_count()

    def sequences_count(self) -> int:

        return self._type_sequences.sequences_count()

    def shots_count(self) -> int:

        return self._type_sequences.shots_count()

    def get_pathtype_asset(self) -> PathTypeAssetNode:

        return self._type_assets

    def get_pathtype_sequence(self) -> PathTypeSequenceNode:

        return self._type_sequences

    # def set_assets(self, assets: List[AssetNode]):

    #     self._type_assets.set_assets(assets)

    # def set_sequences(self, sequences: List[SequenceNode]):

    #     self._type_sequences.set_sequences(sequences)

    # def get_assets(self) -> List[AssetNode]:

    #     return self._type_assets.get_assets()

    # def get_sequences(self) -> List[SequenceNode]:

    #     return self._type_sequences.get_sequences()


    @staticmethod
    def project_from_sg(sg_project: ShotgridProject) -> Optional['ProjectNode']:

        project_id: Optional[int] = sg_project.get_id()

        if project_id is None or project_id <= 0:
            log.warning(f"Unable to create project: project id '{project_id if project_id is not None else ''}': missing or unusable")
            return None

        project_name: Optional[str] = sg_project.get_name()
        project_division_name: Optional[str] = sg_project.get_division_name() 

        if project_name is None or len(project_name.strip()) == 0:
            log.warning(
                f"Unable to create project: project name '{project_name or ''}': missing or unusable"
            )
            return None
        
        if project_division_name is None or len(project_division_name.strip()) == 0:
            log.warning(
                f"Unable to create project: project division '{project_division_name or ''}': missing or unusable"                
            )
            return None

        project_division: Optional[Division] = Division.get_division_from_text(project_division_name)

        if project_division is None:
            log.warning(
                f"Unable to create project: unable to detect project division from text value: '{project_division_name or ''}'"
            )
            return None

        return ProjectNode(division=project_division, id=project_id, name=project_name.strip())

