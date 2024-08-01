## coding: utf-8

from fastapi import APIRouter, Depends, Request

from common.auth.auth_manager import AuthManager
from common.domain.user import User
from common.logger import log
from level.api.model.index_model import IndexModel

router = APIRouter()

@router.get(
    "/",
    responses={
        200: {"model": IndexModel, "description": "API Index"}
    },
    tags=["index"],
    summary="Returns a json object containing an index to all endpoints and operations.",
    response_model=IndexModel,
    response_model_exclude_none=True,
    response_model_exclude_unset=True
)
async def get_index(request: Request, current_user: User = Depends(AuthManager.from_token)) -> IndexModel:
    """Gets the index to the API """
    ...
    log.debug(f"Resolved user {current_user}")
    return IndexModel.build(req=request)


