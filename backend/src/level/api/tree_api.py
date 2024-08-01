from typing import Optional

from fastapi import HTTPException, Request
from fastapi.routing import APIRouter

from common.api.model.status_model import StatusModel
from common.auth.auth_manager import Permission
from level.api.auth.level_resource import ACTION_VIEW_TREEINFO, LevelResource
from level.api.model.tree_info_model import TreeInfoModel
from level.domain.tree import Tree

router = APIRouter()

from level.api.levels_api import levels_service


@router.get(
    "/tree",
    responses={
        200: {"model": TreeInfoModel, "description": "Tree info returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["info"],
    summary="Retrieves the serviced tree information, including objects counts.",
    response_model=TreeInfoModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_tree_info(    
    req: Request,    
    br: LevelResource = Permission(ACTION_VIEW_TREEINFO, LevelResource),
    ) -> TreeInfoModel:
    """Retrieves the serviced tree information, including objects counts."""
    ...
    
    try:        
        tree: Optional[Tree] = levels_service.get_tree()
    except BaseException:
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if tree is None:        
        raise HTTPException(status_code=404, detail="No tree is currently in service")

    return TreeInfoModel.from_tree(tree, req)

