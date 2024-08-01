# coding: utf-8

from fastapi.routing import APIRouter

from common.api.model.status_model import StatusModel
from common.api.model.build_info_model import BuildInfoModel
from common.build_settings import BuildSettings
from common.domain.build_info import BuildInfo

router: APIRouter = APIRouter()
buildSettings = BuildSettings()


@router.get(
    "/info",
    responses={
        200: {
            "model": BuildInfoModel,
            "description": "Build info returned"
        },
        401: {
            "model": StatusModel,
            "description": "Unauthenticated"
        },
        403: {
            "model": StatusModel,
            "description": "Unauthorized"
        },
    },
    tags=["info"],
    summary="Retrieve build information",
)
async def get_info() -> BuildInfoModel:
    """Retrieves the build information attached to the application currently servicing requests"""
    ...

    build_info_model: BuildInfoModel = BuildInfoModel.from_build_info(
        BuildInfo(buildSettings))

    return build_info_model
