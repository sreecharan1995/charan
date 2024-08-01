# coding: utf-8

from typing import List

from fastapi import APIRouter

from common.api.model.status_model import StatusModel
from common.domain.site import Site
from level.api.model.site_model import SiteModel

router = APIRouter()


@router.get(
    "/sites",
    response_model=List[SiteModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,    
    responses={
        200: {"model": List[SiteModel], "description": "Site list returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["sites"],
    summary="Retrieves the list of sites",
)
async def list_sites() -> List[SiteModel]:
    """Retrieves the list of all sites available in the system."""
    ...

    return list(map(lambda s: SiteModel(id=s.name, name=s.value), Site.list()))

