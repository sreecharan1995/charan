
from typing import List, Tuple

from fastapi_permissions import Allow, Authenticated  # type: ignore

from common.service.permissions_service import PermissionService

ACTION_VIEW_LEVEL = "levels_view"
ACTION_SYNC_TREE = "levels_sync-tree"
ACTION_VIEW_TREEINFO = "levels_view-tree-info"

class LevelResource():
    """Represents the permissions required to access level models/resources from endpoints
    """

    __actions__ = [ACTION_VIEW_LEVEL, ACTION_SYNC_TREE, ACTION_VIEW_TREEINFO]

    @staticmethod
    def __acl__() -> List[Tuple[str,str,str]]:
        acls = PermissionService.acls_for(LevelResource)
        acls.append((Allow, Authenticated, ACTION_VIEW_LEVEL))
        acls.append((Allow, Authenticated, ACTION_VIEW_TREEINFO))
        return acls