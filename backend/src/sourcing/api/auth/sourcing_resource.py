from typing import List, Tuple

from common.service.permissions_service import PermissionService

ACTION_VIEW_STATS = "sourcing_view-stats"


class SourcingResource:
    """Represents the permissions required to access event sourcing service models/resources from endpoints
    """

    __actions__ = [ACTION_VIEW_STATS]

    @staticmethod
    def __acl__() -> List[Tuple[str, str, str]]:
        acls = PermissionService.acls_for(SourcingResource)
        return acls
