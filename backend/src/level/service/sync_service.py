import time
import uuid
from pathlib import Path
from typing import List, Optional

import jsonpickle  # type: ignore

from common.domain.division import Division
from common.domain.sg.shotgrid_asset import ShotgridAsset
from common.domain.sg.shotgrid_project import ShotgridProject
from common.domain.sg.shotgrid_sequence import ShotgridSequence
from common.logger import log
from common.utils import Utils
from level.domain.node.asset_node import AssetNode
from level.domain.node.asset_type_node import AssetTypeNode
from level.domain.node.division_node import DivisionNode
from level.domain.node.project_node import ProjectNode
from level.domain.node.root_node import RootNode
from level.domain.node.sequence_node import SequenceNode
from level.domain.sync_request import SyncRequest
from level.level_settings import LevelSettings
from level.service.aws.levels_ddb import LevelsDdb
from common.service.sg.shotgrid_service import ShotgridService


class SyncService:
    """Provides the methods to access or renew the levels tree with data from shotgrid and to fulfill tree sync requests.
    """

    _levels_settings: LevelSettings
    _shotgrid: ShotgridService
    _levels_ddb: LevelsDdb

    def __init__(self, settings: LevelSettings = LevelSettings.load()):
        self._levels_settings = settings
        self._shotgrid = ShotgridService(settings)
        self._levels_ddb = LevelsDdb(settings)

    def __get_tree(self) -> Optional[RootNode]:

        t0: int = time.time_ns()
        tags_to_avoid: List[str] = self._levels_settings.LVL_SYNC_FILTER_PROJECT_TAGS_TO_AVOID

        prj_set: Optional[List[str]] = None

        if len(self._levels_settings.LVL_SYNC_RESTRICT_TO_PROJECTS.strip()) > 0:
              prj_set = self._levels_settings.LVL_SYNC_RESTRICT_TO_PROJECTS.split(",")

        sg_projects: Optional[List[ShotgridProject]] = self._shotgrid.find_projects(
            tags_to_avoid, prj_set
        )

        if sg_projects is None:
            return None
        
        projects: List[ProjectNode] = list( filter( lambda p: p is not None, map(lambda i: ProjectNode.project_from_sg(i), sg_projects)))  # type: ignore
        
        for p in projects:
            
            asset_types: List[AssetTypeNode] = []

            sg_project_assets: Optional[
                List[ShotgridAsset]
            ] = self._shotgrid.find_project_assets(p.get_id())

            if sg_project_assets is None:
                log.warning(
                    f"Interrupting tree building: unable to get assets for project {p.get_id()} '{p.get_name()}'"
                )
                return None

            project_assets: List[AssetNode] = list( filter( lambda a: a is not None, map(lambda i: AssetNode.asset_from_sg(i), sg_project_assets) ))  # type: ignore

            for a in project_assets:

                a_type: str = a.get_type()

                a_type_node: Optional[AssetTypeNode] = next(
                    filter(lambda at: at.get_asset_type() == a_type, asset_types), None
                )

                if a_type_node is None:
                    a_type_node = AssetTypeNode()
                    a_type_node.set_asset_type(a_type)
                    asset_types.append(a_type_node)

                a_type_node.add_asset(a)

            p.get_pathtype_asset().set_asset_types(asset_types)

            sg_project_sequences: Optional[
                List[ShotgridSequence]
            ] = self._shotgrid.find_project_sequences(p.get_id())

            if sg_project_sequences is None:
                log.warning(
                    f"Interrupting tree building: unable to get sequences+shots for project {p.get_id()} '{p.get_name()}'"
                )
                return None
            
            project_sequences: List[SequenceNode] = list( filter( lambda s: s is not None, map(lambda i: SequenceNode.sequence_from_sg(i), sg_project_sequences)))  # type: ignore

            p.get_pathtype_sequence().set_sequences(project_sequences)

            log.info(
                f"Project {p.get_id()} '{p.get_name()}' [{p.get_division().value}] contains {p.assets_count()} assets, and {p.shots_count()} shots in {p.sequences_count()} sequences"
            )

        divisions: List[DivisionNode] = []

        for d_type in Division:
            d_projects: List[ProjectNode] = list(
                filter(lambda p: p.get_division() == d_type, projects)
            )
            division = DivisionNode(d_type)
            division.set_projects(d_projects)
            divisions.append(division)

        log.debug(f"Timing - Traversed shotgrid building nodes in {Utils.time_since(t0, True)}")
        return RootNode(divisions)

    def new_sync_request(self, comment: Optional[str] = "") -> Optional[SyncRequest]:

        sync_request = self._levels_ddb.new_sync_request(comment)

        if sync_request is not None:
            log.debug(
                f"Created new sync request {sync_request.id}, comment '{sync_request.comment}'"
            )

        return sync_request

    def get_sync_requests(self) -> List[SyncRequest]:

        requests: Optional[
            List[SyncRequest]
        ] = self._levels_ddb.get_unfulfilled_sync_requests()

        if requests is None:
            return []

        return requests

    def new_tree(self) -> Optional[str]:

        # self._shotgrid.list_fields("Shot")

        log.info("Traversing shotgrid to build tree")

        root_node: Optional[RootNode] = self.__get_tree()

        if root_node is None:
            return None

        filename: str = f"{uuid.uuid4().hex}.sgtree"

        self.__save_tree(root_node, filename)

        return filename

    def __save_tree(self, tree: RootNode, filename: str) -> bool:

        target_filename: str = str(Path(self._levels_settings.LVL_TREE_BASEPATH, filename))

        try:
            with open(target_filename, "w") as json_file:
                json_data: str = jsonpickle.encode(tree, unpicklable=True, keys=True)  # type: ignore
                json_file.write(json_data)
                # json.dump(json_data, json_file, ensure_ascii = True, skipkeys=False, check_circular=True, allow_nan=False, cls=None, indent=None, separators=None)
        except Exception as e:
            log.error(f"Tree serialization failed: {e}")
            return False

        return True

    def __load_tree(self, filename: str) -> Optional[RootNode]:

        log.debug(f"Loading tree from snapshot file {filename}")

        source_filename: str = str(Path(self._levels_settings.LVL_TREE_BASEPATH, filename))

        try:
            with open(source_filename, "r") as json_file:
                json_data = json_file.read()
                tree: Optional[RootNode] = jsonpickle.decode(json_data)  # type: ignore
            return tree
        except Exception as e:
            log.error(f"Tree deserialization failed: {e}")

        return None

    def verify_tree(self, filename: str) -> bool:

        return self.__verified_tree(filename) is not None

    def __verified_tree(self, filename: str) -> Optional[RootNode]:

        tree: Optional[RootNode] = self.__load_tree(filename)

        if tree is None:
            log.warning(f"Failed to load tree from '{filename}'")
        else:
            verified: bool = self.__verify_tree(filename, tree)
            if verified:
                return tree

        return None

    def __verify_tree(self, filename: str, tree: RootNode) -> bool:

        try:
            projects_count = tree.projects_count()
            if projects_count == 0:
                log.warning(f"Tree '{filename}' is loadable, but has no projects")
            else:
                log.info(
                    f"Verified tree '{filename}'. Has {tree.assets_count()} assets in {projects_count} projects, and {tree.shots_count()} shots in {tree.sequences_count()} sequences"
                )
                return True
        except BaseException:
            log.warning(f"Tree '{filename}' is corrupted or unusable")

        return False

    def load_tree(self, filename: str) -> Optional[RootNode]:

        return self.__verified_tree(filename)

    def get_last_fulfilled_sync_request(self) -> Optional[SyncRequest]:

        log.debug(f"Looking up for the latest fulfilled sync request")
        return self._levels_ddb.get_last_fulfilled_request()

    def is_latest_tree_snapshot(self, filename: str) -> bool:

        last_fulfilled_request = self.get_last_fulfilled_sync_request()

        if last_fulfilled_request is None:
            return False  # assume is not the same

        return filename == last_fulfilled_request.filename    

    def fulfill_requests(self, filename: str, requests: List[SyncRequest]) -> int:

        log.info(
            f"Fulfilling {len(requests)} requests using data from filename {filename}"
        )

        fulfilled: int = 0

        for request in requests:

            id: int = request.id

            if id is None:
                log.warning(
                    "Failed to fulfill request, misses key attribute"
                )  # should not happen
                continue

            if self._levels_ddb.update_request_filename(id, filename):
                log.debug(f"Fulfilling request {id}")
                fulfilled = fulfilled + 1
            else:
                log.warning(f"Failed to fulfill request {id}")

        return fulfilled
