# coding: utf-8

from fastapi import APIRouter, HTTPException, Path, Query, Request

from common.api.model.page_model import PageModel
from common.api.model.status_model import StatusModel
from common.auth.auth_manager import Permission
from dependency.api.auth.package_resource import (ACTION_VIEW_PACKAGE,
                                                  PackageResource)
from dependency.api.model.package_model import PackageModel
from dependency.dependency_settings import DependencySettings
from dependency.service.package_service import PackageService

package_service = PackageService()
router = APIRouter()
settings: DependencySettings = DependencySettings.load()


@router.get(
    "/packages/{package_name}",
    responses={
        200: {"model": PackageModel, "description": "Package found and returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["packages"],
    summary="Retrieves a package",
    response_model=PackageModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True
)
async def get_package(
        br: PackageResource = Permission(ACTION_VIEW_PACKAGE, PackageResource),
        package_name: str = Path(default=None, required=True, title="name of package",
                                 description="The name of the package to get", example="katana"),
) -> PackageModel:
    """Retrieves a package details, including available versions, using its identifying name"""
    ...
    package = package_service.get_package(package_name)

    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    return package


@router.get(
    "/packages",
    response_model=PageModel[PackageModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": PageModel[PackageModel], "description": "List of packages returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["packages"],
    summary="Retrieves a list of available packages"
)
async def list_packages(
        req: Request,
        br: PackageResource = Permission(ACTION_VIEW_PACKAGE, PackageResource),
        p: int = Query(default=1, title="page number", description="The page to return. First page is 1.", ge=1),
        ps: int = Query(default=settings.DEFAULT_PAGE_SIZE, title="page size",
                        description="The number of elements in a page.", ge=10),
        q: str = Query(default=None, title="a term", description="The term to filter names by"),
        c: str = Query(default=None, title="a category", description="The term to filter categories by")
) -> PageModel[PackageModel]:
    """Retrieves a paginated and optionally filtered list of packages available in the system."""
    ...
    items, total = package_service.list_packages(p, ps, q, c)
    return PageModel.build(req, items, total, p, ps, q)
