
from typing import List, Tuple

from common.service.permissions_service import PermissionService

ACTION_VIEW_BUNDLE = "swds_view-bundles"
ACTION_UPDATE_BUNDLE = "swds_update-bundle"
ACTION_CREATE_BUNDLE = "swds_create-bundle"
ACTION_DELETE_BUNDLE = "swds_delete-bundle"

class BundleResource():
    """Represents the permissions required to access bundle models/resources from endpoints
    """

    __actions__ = [ACTION_VIEW_BUNDLE, ACTION_UPDATE_BUNDLE, ACTION_CREATE_BUNDLE, ACTION_DELETE_BUNDLE]

    @staticmethod
    def __acl__() -> List[Tuple[str,str,str]]:
        return PermissionService.acls_for(BundleResource)