## coding: utf-8

from fastapi.routing import APIRouter

from common.api.model.auth_info_model import AuthInfoModel
from common.auth.auth_settings import AuthSettings

router: APIRouter = APIRouter()
authSettings = AuthSettings.load_auth()


@router.get(
    "/auth_info",
    responses={
        200: {"model": AuthInfoModel, "description": "Auth info returned"}
    },
    tags=["info"],
    summary="Retrieve auth configuration information",
)
async def get_auth_info() -> AuthInfoModel:
    """Retrieves the information needed in clients to setup authentication"""
    ...
    authInfo = AuthInfoModel()
    authInfo.client_id = authSettings.AUTH_CLIENT_ID
    authInfo.tenant_id = authSettings.AUTH_TENANT_ID

    return authInfo
