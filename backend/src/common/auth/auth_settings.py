from typing import List, Dict

from functools import lru_cache

from pydantic import BaseSettings

from common.logger import log


class AuthSettings(BaseSettings):
    """Represents the set of configurable env vars related to auth, groups, permissions, etc
    """

    # the following vars must hold the credentials used to connect and use the remote oauth service
    AUTH_URL: str = ""
    AUTH_TOKEN_URL: str = ""
    AUTH_REFRESH_URL: str = ""
    AUTH_JWKS_URL: str = ""
    AUTH_CLIENT_ID: str = ""
    AUTH_TENANT_ID: str = ""

    
    AUTH_USE_HARDCODED_GROUPS: bool = False
    """When true token auth is bypassed and all known hardcoded groups will be assigned to the calling user
    """
    
    AUTH_TOKEN_ENFORCE_EXP: bool = True
    """When true, which is the default and production useful value, the token expiration date is enforced. 

    During local development, a False value may be used to avoid token to be manually being refreshed.
    """

    AUTH_PERMISSION_CSV_FILE: str = "src/common/auth/permissions.csv"
    """Route to file holding the permissions CSV file.
    """

    AUTH_GROUP_MAPPINGS_CSV_FILE: str = "src/common/auth/group_mappings.csv"
    """Route to file holding the groups mapping file.
    """

    AUTH_APIKEY_GROUPS: Dict[str,List[str]] = dict()
    """Dict holding as key an apikey and as value a list of group/roles.
     
    The group list used to grant authorization or not to microservices that use the apikey as a 
    mean to authenticate themselves.
    """

    PERMISSIONS_MATRIX_CACHE_TTL: int = 60
    """The permission matrix data is cached for this number of seconds before being reloaded from file
    """

    GROUP_MAPPINGS_CACHE_TTL: int = 60
    """The groups mapping data is cached for this number of seconds before being reloaded from file
    """

    def __init__(self):
        log.debug("Loading AUTH settings")
        super(AuthSettings, self).__init__()  # type: ignore

    @staticmethod
    @lru_cache()
    def load_auth() -> 'AuthSettings':
        return AuthSettings()
