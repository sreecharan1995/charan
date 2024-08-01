import csv
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

import jwt
from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException
from fastapi_permissions import (Authenticated, Everyone,  # type: ignore
                                 configure_permissions)
from jwt import PyJWKClient, PyJWTError
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from common.auth.auth_schema import AuthSchema
from common.auth.auth_settings import AuthSettings
from common.domain.user import User
from common.logger import log
from common.service.permissions_service import settings

"""
If signature fails to validate when using azure ad, make sure the token is being requested with scopes:
    email profile openid {{CLIENT_ID}}/.default

See more info here: https://github.com/AzureAD/microsoft-authentication-library-for-js/issues/521#issuecomment-577400515
"""

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail={'code': 401, 'message': "Unauthorized"},
    headers={"WWW-Authenticate": "Bearer"},
)

PERMISSIONS_EXCEPTION = HTTPException(
    status_code=HTTP_403_FORBIDDEN,
    detail={'code': 403, 'message': "Insufficient permissions"},
    headers={"WWW-Authenticate": "Bearer"},
)

APIKEY_PREFIX: str = "apikey:"

auth_settings = AuthSettings.load_auth()


class AuthManager:
    """This class has methods to decode jwt tokens and decide about the authorization of groups/roles in tokens.
    """

    _settings: AuthSettings

    DEFAULT_ALGORITHMS = ["RS256"]

    # These groups will be coming in the jwt
    # GROUPS: Set[str] = {
    #     "sg_permission_admin",
    #     "sg_permission_pipeline",
    #     "sg_permission_pipeline_manager,"
    #     "sg_permission_producer",
    #     "sg_permission_production_manager",
    #     "sg_permission_production",
    #     "sg_permission_supervisor",
    #     "sg_permission_artist",
    #     "sg_permission_editorial",
    #     "sg_permission_lead"
    # }

    def __init__(self) -> None:
        self._settings = AuthSettings.load_auth()

    @staticmethod
    @lru_cache()
    def instance() -> 'AuthManager':
        return AuthManager()

    @lru_cache()
    def get_jwks_client(self) -> PyJWKClient:
        jwks_url = self._settings.AUTH_JWKS_URL
        log.debug("JWKS: using: %s", jwks_url)
        return PyJWKClient(jwks_url)

    @staticmethod
    def from_token(token: Optional[str] = Depends(AuthSchema.get_schema())) -> User:
        """Method called from endpoints when requiring token-based auth, and returning an actual or internal user.

        The returned user includes the groups/roles it belongs to.
        """
        
        return AuthManager.instance()._from_token(token)  # type: ignore

    def _from_token(self, token: str) -> User:
        """Internal method to actually decode the incoming jwt token or apikey.

        The token may even be ignored completely or apikey auth fails. 
        
        Apikey auth is used by microservices when the call is performed from one of them.

        This method depends on configured env vars to decide if 
        actually perform authenticacion or not, which is handy during development.
        """

        if self._settings.AUTH_USE_HARDCODED_GROUPS:
            log.debug("Impersonating calling user to have all rights. Switch property AUTH_USE_HARDCODED_GROUPS to "
                      "false if you wish to disable this behavior.")
            return User(username="disabled", email="disabled@disabled.local", full_name="Disabled",
                        groups=self._all_group_names(), token=token)

        if token.startswith("apikey:"):
            log.debug("Using APIKEY token to authenticate caller. Switch property AUTH_USE_APIKEY to false if you wish to disable this behavior.")
            return User(username="apikey", email="", full_name="", groups=self._apikey_group_names(token), token=token)

        data: Dict[Any, Any] = self.decode_token(token)
        user: User = User(
            username=data.get("unique_name", ""),
            email=data.get("upn", None),
            full_name=data.get("name", None),
            groups=self._parse_groups(data.get("roles", set())),
            projects=data.get("projects") or set(),
            token=token
        )

        if user.username == "" or user.email is None or user.full_name is None:
            raise HTTPException(status_code=401, detail="Authenticated user lacks required data fields")

        return user

    def decode_token(self, token: str) -> Dict[Any, Any]:
        """Decodes a string encoding a jwt token.
        """
        try:
            log.debug(f"JWKS: decoding token '{token}'")
            signing_key = self.get_jwks_client().get_signing_key_from_jwt(token)
            log.debug(f"JWKS: resolved key id {signing_key.key_id}")  # type: ignore
            data = jwt.decode(  # type: ignore
                jwt=token,
                key=signing_key.key,  # type: ignore
                algorithms=self.DEFAULT_ALGORITHMS,
                audience=self._settings.AUTH_CLIENT_ID,
                options={"verify_exp": self._settings.AUTH_TOKEN_ENFORCE_EXP, "verify_signature": True},
            )
            log.debug("JWKS: decoded token as: %s", dict(data))
            return data
        except PyJWTError as token_error:
            log.debug(f"JWKS: token validation failed: {token_error}")
            raise CREDENTIALS_EXCEPTION
        except BaseException as e:
            log.warning(f"JWKS: error decoding token: {e}")
            raise CREDENTIALS_EXCEPTION

    @staticmethod
    def permission(action: str, resource: object):
        return configure_permissions(get_active_principals, PERMISSIONS_EXCEPTION)(action, resource)


    @cached(cache=TTLCache(maxsize=1, ttl=settings.GROUP_MAPPINGS_CACHE_TTL))  # type: ignore
    def _group_mappings(self) -> Dict[str, str]:
        """
        Reads and caches the groups mapping csv file. The file is read from property AUTH_GROUP_MAPPINGS_CSV_FILE
        :return: a Dict where keys are group ids and values are group names
        """
        log.debug("Refreshing group mappings")
        mappings: Dict[str, str] = {}
        with open(settings.AUTH_GROUP_MAPPINGS_CSV_FILE) as csvfile:
            reader = csv.reader(csvfile)
            lines = [line for line in reader]
            for row in lines:
                if len(row) is 2:
                    mappings[row[1]] = row[0]
                else:
                    log.warning("Found invalid row in group mappings file.")
            log.debug(f"Resolve group mappings as: \n {mappings}")
            return mappings

    def _parse_groups(self, jwt_roles: Set[str]) -> Set[str]:
        """
        Receives a list of group ids coming in the JWT token and resolves the name for each of them.
        The names are resolved from a csv file that has group_ids and group names for each possible group.

        :param jwt_roles: a set of str representing the group ids.
        :return: a set of str where each element is a group name
        """
        if len(jwt_roles) == 0:
            return set()

        groups: Set[str] = set()
        for role_id in jwt_roles:
            role: Optional[str] = self._group_mappings().get(role_id)
            if role is not None:
                groups.add(role)

        return groups


    def _all_group_names(self) -> Set[str]:
        """
        Returns all known group names based on group mappings file.
        """
        return set(self._group_mappings().values())

    def _apikey_group_names(self, apikey: Optional[str] = None) -> Set[str]:
        """
        Returns all apikey groups, if also is a known group name, based on group mappings file.

        Apikey groups are the group/roles authorized for a specific apikey.
        """        

        if apikey is None or len(apikey.strip()) == 0 or not apikey.startswith(APIKEY_PREFIX):
            return set()

        apikey = apikey[len(APIKEY_PREFIX):] # set to the actual api key

        groups: List[str] = self._settings.AUTH_APIKEY_GROUPS.get(apikey, []) # lookup the configured groups for this api key

        return set(groups).intersection(set(self._group_mappings().values())) # return only known groups according to perms matrix file


# NOTICE: already attempted to put this code as a static method of AuthManager but didn't worked
# however it currently works as is
def get_active_principals(user: User = Depends(AuthManager.from_token)) -> List[Any]:
    if user:
        # user is logged in
        principals = [Everyone, Authenticated]
        principals.extend(getattr(user, "groups", []))
    else:
        # user is not logged in
        principals = [Everyone]
    return principals


Permission = AuthManager.permission
