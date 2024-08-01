import time
from typing import Optional

from fastapi import Depends, HTTPException, Query, Request
from fastapi.routing import APIRouter

from common.api.model.status_model import StatusModel
from common.auth.auth_manager import AuthManager, Permission
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.user import User
from common.logger import log
from common.utils import Utils
from level.api.auth.level_resource import ACTION_VIEW_LEVEL, LevelResource
from level.api.model.level_model import LevelModel
from level.domain.tree_level import TreeLevel
from level.level_settings import LevelSettings
from level.service.levels_service import LevelsService

router = APIRouter()

settings: LevelSettings = LevelSettings.load()
levels_service: LevelsService = LevelsService(settings)


@router.get(
    "/levels",
    responses={
        200: {"model": LevelModel, "description": "Level found and returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["levels"],
    summary="Retrieves a level from the levels hierarchy.",
    response_model=LevelModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_level(
    req: Request,
    br: LevelResource = Permission(ACTION_VIEW_LEVEL, LevelResource),
    user: User = Depends(AuthManager.from_token),
    depth: int = Query(
        default=1,
        title="max-depth os sub-level nesting",
        description="The max number of nesting for sub-levels.",
        example=0
    ),
    path: str = Query(
        default="/",
        title="path of level",
        description="The path that points to the level to get.",
        example="/toronto/television"
    ),
) -> LevelModel:
    """Retrieves a level node from the hierarchy of levels"""
    ...

    parsed_path: Optional[ParsedLevelPath] = ParsedLevelPath.from_level_path(LevelPath.from_path(path))

    if parsed_path is None:
        raise HTTPException(status_code=400, detail="The path syntax is incorrect")

    if depth < 0:
        raise HTTPException(status_code=400, detail="The depth value is unaceptable")

    try:        
        t: int = time.time_ns()
        tree_level: Optional[TreeLevel] = levels_service.get_level(parsed_path=parsed_path, max_depth=depth if depth != 0 else 1, operator_user=user)
        log.debug(f"Timing - Got level in {Utils.time_since(t, True)} seconds")
    except BaseException:
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if tree_level is None:        
        raise HTTPException(status_code=404, detail="Level not found")

    t: int = time.time_ns()
    level_mode: LevelModel = LevelModel.from_tree_level(tree_level, depth, req)
    log.debug(f"Timing - Got level model in {Utils.time_since(t, True)} seconds")

    return level_mode
