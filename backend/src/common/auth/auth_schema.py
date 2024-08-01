# from functools import lru_cache
from functools import lru_cache
from common.auth.auth_settings import AuthSettings
from fastapi.security import OAuth2AuthorizationCodeBearer


class AuthSchema:
    """Represents oauth scheme data set up from configuration.
    """

    _oauth2_scheme: OAuth2AuthorizationCodeBearer

    def __init__(self):
        settings = AuthSettings.load_auth()
        self._oauth2_scheme = OAuth2AuthorizationCodeBearer(
            authorizationUrl=settings.AUTH_URL,
            tokenUrl=settings.AUTH_TOKEN_URL,
            refreshUrl=settings.AUTH_REFRESH_URL,
            scopes={"email": "", "profile": "", "openid": "", f"{settings.AUTH_CLIENT_ID}/.default": ""}
        )

    @staticmethod
    @lru_cache()
    def instance() -> 'AuthSchema':
        return AuthSchema()

    @staticmethod
    def get_schema() -> OAuth2AuthorizationCodeBearer:
        return AuthSchema.instance()._oauth2_scheme
