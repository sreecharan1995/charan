## coding: utf-8

from fastapi import APIRouter, Request

from dependency.api.model.index_model import IndexModel

router = APIRouter()


@router.get(
    "/",
    responses={
        200: {"model": IndexModel, "description": "API Index"}
    },
    tags=["info"],
    summary="Returns a json object containing an index to all endpoints and operations.",
    response_model=IndexModel,
    # response_model_exclude_none=True,
    # response_model_exclude_unset=True
)
async def get_index(request: Request) -> IndexModel:
    """Gets the index to the API """
    ...
    return IndexModel.build(req=request)
