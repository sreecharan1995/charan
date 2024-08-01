import csv
from typing import Any, Dict, List, Set, Tuple

from cachetools import TTLCache, cached
from fastapi_permissions import Allow  # type: ignore

from common.auth.auth_settings import AuthSettings
from common.domain.user import User
from common.logger import log

settings = AuthSettings.load_auth()

"""
A Permissions matrix has roles or groups as the first column and actions as the rest of the columns. 
For each role there will be a row in the matrix. Here is an example:

matrix = {
    "Admin": ["swds_create-profile", "swds_update-profile", "swds_view_profile", "swds_create-bundle"],
    "Pipeline": ["swds_create-profile", "swds_update-profile", "swds_view_profile", "swds_create-bundle"],
    "Manager-Pipeline": ["swds_create-profile", "swds_update-profile", "swds_view_profile", "swds_create-bundle"],
    "Producer": ["swds_view_profile"]
}

"""


@cached(cache = TTLCache(maxsize=1, ttl=settings.PERMISSIONS_MATRIX_CACHE_TTL)) # type: ignore
def matrix() -> Dict[str, List[str]]:
    log.debug("Refreshing permissions matrix")
    a_matrix: Dict[str, List[str]] = {}
    with open(settings.AUTH_PERMISSION_CSV_FILE) as csvfile:
        reader = csv.reader(csvfile)
        # list_of_list = []
        # j = 0
        lines = [line for line in reader]
        actions = lines[0][1:]
        for _ in range(len(actions)):
            for row in lines[1:]:
                a_matrix[row[0]] = []
                for action_index in range(len(actions)):
                    if row[action_index + 1] == 'X':
                        a_matrix[row[0]].append(actions[action_index])
        log.debug(f"Resolve permission matrix as: \n {a_matrix}")
        return a_matrix


class PermissionService:
    """Methods to determine user permissions from group/roles and read required permissions from acl based resources.
    """

    @staticmethod
    def get_user_permissions(user: User) -> Set[str]:
        user_groups = user.groups
        result: Set[str] = set()
        if user_groups is not None:
            g: str
            for g in user_groups:
                if matrix().get(g) is not None:
                    result.update(matrix()[g])
        return result

    @staticmethod
    def acls_for(resource: object) -> List[Tuple[str, str, str]]:

        # log.debug(f"ACLs for {resource}")

        acls: List[Tuple[str, str, str]] = []

        resource_actions: Any = getattr(resource,
                                        "__actions__")  # TODO: raises exception if no __actions__ is present ??
        log.debug(f"{repr(resource)} resource actions: {resource_actions}")

        role: str
        for role in matrix().keys():
            action: str
            for action in resource_actions:
                if action in matrix()[role]:
                    acls.append((Allow, role, action))

        log.debug(f"{repr(resource)} resource acls: {acls}")

        return acls
    
    @staticmethod
    def retrieve_token_for_person(person: str) -> str:
        return "" # TODO: TBI
