
from typing import List, Tuple

from common.service.permissions_service import PermissionService

ACTION_VIEW_PACKAGE = "swds_view-packages"

class PackageResource():
    """Represents the permissions required to access package models/resources from endpoints
    """

    __actions__ = [ACTION_VIEW_PACKAGE]

    @staticmethod
    def __acl__() -> List[Tuple[str,str,str]]:
        return PermissionService.acls_for(PackageResource)