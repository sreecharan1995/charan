from typing import List, Tuple

from common.service.permissions_service import PermissionService

ACTION_CREATE_PROFILE = "swds_create-profile"
ACTION_DELETE_PROFILE = "swds_delete-profile"
ACTION_VIEW_PROFILE = "swds_view-profile"
ACTION_UPDATE_PROFILE = "swds_update-profile"


class ProfileResource:
    """Represents the permissions required to access profile models/resources from endpoints
    """
    
    __actions__: List[str] = [ACTION_CREATE_PROFILE, ACTION_DELETE_PROFILE, ACTION_VIEW_PROFILE, ACTION_UPDATE_PROFILE]

    @staticmethod
    def __acl__()-> List[Tuple[str,str,str]]:
        return PermissionService.acls_for(ProfileResource)