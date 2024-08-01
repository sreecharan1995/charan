import time
from typing import Optional

from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.user import User
from common.logger import log
from level.domain.node.base_node import BaseNode
from level.domain.node.root_node import RootNode
from level.domain.sync_request import SyncRequest
from level.domain.tree import Tree
from level.domain.tree_explorer import TreeExplorer
from level.domain.tree_level import TreeLevel
from level.level_settings import LevelSettings
from level.service.sync_service import SyncService


class LevelsService:
    """Provides the methods to access the latest levels tree and to access/search levels based on paths.
    """

    _settings: LevelSettings
    _sync_service: SyncService
    _tree: Optional[Tree] = None
    _latest_check: float = 0

    def __init__(self, settings: LevelSettings = LevelSettings.load()):
        self._settings = settings
        self._sync_service = SyncService(settings)

    def get_tree(self) -> Tree:

        return self.__get_tree()

    def __get_tree(self) -> Tree:

        # TODO: TBI: sync access to this method

        previous_tree: Optional[Tree] = self._tree
        check_time: int = time.time_ns()
        check_now: bool = False
        cache_seconds: int = self._settings.LVL_API_TREE_CACHE_MIN_SECONDS
        latest_sync_request = None
        latest_check: float = self._latest_check        

        if self._tree is None:
            check_now = True
        else:
            passed_time: float = check_time - latest_check
            remaining_time: float = (cache_seconds * 10**9) - passed_time

            if remaining_time > 0: # ...so, cached tree is still usable
                log.debug(
                    f"Check for younger tree delayed for {remaining_time / 10**9} seconds"
                )
            else:
                log.debug(f"Cached tree expired {-1 * remaining_time / 10**9} seconds ago") # negative
                check_now = True  # because cached is old

        if check_now: # cached expired or no tree available

            latest_sync_request = self._sync_service.get_last_fulfilled_sync_request()
            self._latest_check = check_time

            if latest_sync_request is None:
                log.warning("Unable to detect the latest tree for service")
            elif previous_tree is None or previous_tree.is_older_than(latest_sync_request.id):
                self.__attempt_tree_switch(latest_sync_request)

        effective_tree: Optional[Tree] = self._tree

        if effective_tree is None: 
            raise Exception("No tree is available for service")

        actually_using_cached: bool = (
            previous_tree is not None
            and previous_tree.get_sync_request().id == effective_tree.get_sync_request().id
        )

        message: str = f"Using {'cached' if actually_using_cached else 'fresh'} tree snapshot {effective_tree.get_filename() if self._tree is not None else ''}"

        if actually_using_cached:
            log.debug(message)
        else:
            log.info(message)

        return effective_tree

    def __attempt_tree_switch(self, sync_request: SyncRequest):

        # TODO: TBI: attempt a synchronized switch of the tree in another thread to avoid slowing down the request, and..
        # TODO: TBI: block current request only if there is no tree in service

        filename: str = sync_request.filename
        root_node: Optional[RootNode] = self._sync_service.load_tree(filename)

        if root_node is None:
            log.warning("Failed to load latest available tree for service")
        else:
            root_node.prepare_for_service()  # fill parents, etc

            self._tree = Tree(root_node, sync_request)

            log.debug(
                f"Switched service to use tree from snapshot {self._tree.get_filename()}"
            )

    def get_level(self, parsed_path: ParsedLevelPath, max_depth: int, operator_user: User) -> Optional[TreeLevel]:

        tree: Tree = self.get_tree()

        explorer: TreeExplorer = TreeExplorer(tree)

        node: Optional[BaseNode] = explorer.find_node_by_path(parsed_path)

        if node is None:
            return None
                
        level: TreeLevel = node.as_level(max_depth)        

        if not self.has_user_acccess_to_level(level, operator_user):
            return None

        return level

    def has_user_acccess_to_level(self, level: TreeLevel, operator_user: User) -> bool:

        if level.project is None:
            return True # levels above projects are permitted

        if self._settings.LVL_ENFORCE_PROJECT_ACCESS_SECURITY:

            if operator_user.projects is None:
                log.warning(f"No projects found in user token. Blocked user '{operator_user.username}' attempt to access project '{level.project}' path '/{level.path}'")
                return False

            if not level.project in operator_user.projects:
                log.info(f"Blocked user '{operator_user.username}' attempt to access unauthorized project '{level.project}' path '/{level.path}'")
                return False
        
        else:
            log.warning(f"Project access control is not being enforced according to settings")

        log.debug(f"Letting user '{operator_user.username}' access to project '{level.project}' path '/{level.path}'")

        return True

