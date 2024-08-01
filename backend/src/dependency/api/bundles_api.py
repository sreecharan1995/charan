# coding: utf-8

from typing import List, Optional

from fastapi import (APIRouter, Body, HTTPException, Path, Query, Request,
                     Response)

from common.api.model.page_model import PageModel
from common.api.model.status_model import StatusModel
from common.auth.auth_manager import Permission
from dependency.api.auth.bundle_resource import (ACTION_CREATE_BUNDLE,
                                                 ACTION_DELETE_BUNDLE,
                                                 ACTION_UPDATE_BUNDLE,
                                                 ACTION_VIEW_BUNDLE,
                                                 BundleResource)
from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.service.bundle_service import BundleService

bundle_service = BundleService()

router = APIRouter()


@router.get(
    "/bundles/{bundle_name}",
    response_model=BundleModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": BundleModel, "description": "Successful response"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["bundles"],
    summary="Retrieve a bundle from the bundles library",
)
async def get_bundle(
    br: BundleResource = Permission(ACTION_VIEW_BUNDLE, BundleResource),
    bundle_name: str = Path(None, title="name of bundle", description="The name of the bundle to get", example="maya_dev"),
) -> BundleModel:
    """Returns a bundle from the bundles library using its identifying name
    
    A bundle is a non-modifiable set of packages that is given a name and can be used when creating profiles. Specifically a copy of the bundle properties 
    can be attached to profiles. Internally, the bundle name is used to recover is properties from the library, then these are copied as a "new" bundle with the same
    name but attached to the profile and independent from the original available bundle in the library.
    """

    return bundle_service.get_bundle(bundle_name)


@router.get(
    "/bundles",
    response_model=PageModel[BundleModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": List[BundleModel], "description": "Successful response"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["bundles"],
    summary="Retrieves a paginated list of available bundles",
)
async def list_bundles(    
    req: Request,
    br: BundleResource = Permission(ACTION_VIEW_BUNDLE, BundleResource),
    p: int = Query(default=None, title="page number", description="The page number to return. First page is 1.", ge=1, example=1),
    ps: int = Query(default=None, title="page size", description="The number of elements per page.", ge=10, example=10),
    q: Optional[str] = Query(default=None, title="term to filter by", description="The term to filter by", example="maya"),
) -> PageModel[BundleModel]:
    """Retrieves a paginated list of bundles in the library.

    Each bundle has a unique name and a set of packages. Each package has a name and a version. Bundles are stored in the bundles library and can be reused when attaching 
    them to profiles.
    """
    ...
    items, total = bundle_service.list_bundles(p, ps, q)

    return PageModel.build(req, items, total, p, ps, q)


@router.post(
    "/bundles",
    status_code=201,
    response_model=BundleModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        201: {"model": BundleModel, "description": "Bundle created successfully and returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["bundles"],
    summary="Adds a new bundle to the bundles library",
)
async def create_bundle(
    br: BundleResource = Permission(ACTION_CREATE_BUNDLE, BundleResource),
    bundle: BundleModel = Body(..., description="The payload to create a bundle")
) -> Optional[BundleModel]:
    """Adds a new bundle to the bundles library.
    
    Bundles in the library can be later used when attaching them to profiles. The original is kept in the library, available for re-usage, only 
    a copy of its properties is attached to the profiles.    
    """
    b: Optional[BundleModel] = bundle_service.create_bundle(bundle)

    if b is None:
        raise HTTPException(status_code=500, detail="Failed to create bundle or to confirm that it was created")

    return b

@router.put(
    "/bundles/{bundle_name}",
    response_model=BundleModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": BundleModel, "description": "Successful replacement, bundle returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["bundles"],
    summary="Replace the list of packages for a bundle",
)
async def set_bundle_packages(
    br: BundleResource = Permission(ACTION_UPDATE_BUNDLE, BundleResource),
    bundle_name: str = Path(None, required=True, title="name of bundle", description="The name of the bundle getting its packages replaced", example="maya_dev"),
    pkref_list: List[PackageReferenceModel] = Body(
        default=None, required=True, title="list of package references", description="The list of package references to replace the one in the bundle", example=[ { "name": "ocio", "version": "1.16.0" } ]
    ),
) -> BundleModel:
    """Replaces the list of package references in a library bundle.
    
    A bundle in the library has a name and a set of packages. This package set (or list) can be replaced. When a bundle is attached to a profile a copy of the current name and 
    packages is made and included in the profile. Future modifications on the bundle in the library doesn't affect the previously copied data already in the profile.
    """
    ...    
    if pkref_list is None:
        raise HTTPException(status_code=422, detail="Body is empty")

    prev = bundle_service.get_bundle(bundle_name)

    if prev is None:
        raise HTTPException(status_code=404, detail="Bundle not found")

    bundle = bundle_service.update_bundle_packages(bundle_name, pkref_list)

    return bundle


@router.delete(
    "/bundles/{bundle_name}",
    status_code=204,
    response_class=Response,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        204: {"model": None, "description": "Bundle deleted successfuly."},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["bundles"],
    summary="Deletes a bundle from the library",
)
async def delete_bundle(
    br: BundleResource = Permission(ACTION_DELETE_BUNDLE, BundleResource),
    bundle_name: str = Path(default=None, required=True, title="name of bundle", description="The name of the bundle to delete"),
):
    """Deletes a bundle from the bundles library.
    
    When a bundle is removed from the library, profiles that include this bundle in the past are not affected, only new profiles won't be able to include
    the deleted bundle, and its name will be available as a potentially new bundle if another one is created (probably using another set of packages)
    """

    bundle_service.delete_bundle(bundle_name)