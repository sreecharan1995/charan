from typing import List, Tuple

from common.service.permissions_service import PermissionService

ACTION_VIEW_CONFIG = "configs_view-config"
ACTION_CREATE_CONFIG = "configs_create-config"
ACTION_UPDATE_CONFIG = "configs_update-config"
ACTION_DELETE_CONFIG = "configs_delete-config"


class ConfigResource:
    """Represents the permissions required to access configs models/resources from endpoints
    """

    __actions__ = [ACTION_VIEW_CONFIG, ACTION_CREATE_CONFIG, ACTION_UPDATE_CONFIG, ACTION_DELETE_CONFIG]

    @staticmethod
    def __acl__() -> List[Tuple[str, str, str]]:
        acls = PermissionService.acls_for(ConfigResource)
        return acls
