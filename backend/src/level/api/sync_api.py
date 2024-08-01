from fastapi import HTTPException, Query
from fastapi.routing import APIRouter

from common.api.model.status_model import StatusModel
from common.auth.auth_manager import Permission
from level.api.auth.level_resource import ACTION_SYNC_TREE, LevelResource
from level.level_settings import LevelSettings
from level.service.sync_service import SyncService

router = APIRouter()

settings: LevelSettings = LevelSettings.load()
sync_service: SyncService = SyncService(settings)


@router.post(
    "/sync",
    status_code=200,
    responses={
        201: {"model": None, "description": "Sync request created successfully"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["levels"],
    summary="Create a new tree sync request",
)
async def create_sync_request(
    br: LevelResource = Permission(ACTION_SYNC_TREE, LevelResource),
    comment: str = Query(
        default="",
        required=False,
        title="comment for the request",
        description="An optional comment to include in the request",
    ),
) -> StatusModel:
    """Creates a new tree sync request, with optional comment"""
    ...
    sync_request = sync_service.new_sync_request(comment)

    if sync_request is None:
        raise HTTPException(
            status_code=500, detail="Failed to create a new sync request"
        )

    return StatusModel(code=200, message="Levels Sync Requested")
