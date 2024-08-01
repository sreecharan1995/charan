# coding: utf-8

from typing import Any

import json
from operator import attrgetter
from typing import List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Path, Query,
                     Request, Response, UploadFile)

from common.api.model.page_model import PageModel
from common.api.model.status_model import StatusModel
from common.auth.auth_manager import AuthManager, Permission
from common.domain.level_path import LevelPath
from common.domain.user import User
from common.logger import log
from common.service.levels_remote_service import LevelsRemoteService
from dependency.api.auth.profile_resource import (ACTION_CREATE_PROFILE,
                                                  ACTION_DELETE_PROFILE,
                                                  ACTION_UPDATE_PROFILE,
                                                  ACTION_VIEW_PROFILE,
                                                  ProfileResource)
from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.full_profile_model import FullProfileModel
from dependency.api.model.import_summary_model import ImportReport
from dependency.api.model.new_profile_comment_model import \
    NewProfileCommentModel
from dependency.api.model.new_profile_model import NewProfileModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.api.model.patch_profile_model import PatchProfileModel
from dependency.api.model.profile_comment_model import ProfileCommentModel
from dependency.api.model.profile_model import (PROFILE_STATUS_INVALID,
                                                PROFILE_STATUS_VALID,
                                                ProfileModel)
from dependency.api.model.profile_validity_change_model import \
    ProfileValidityEvent
from dependency.dependency_settings import DependencySettings
from dependency.service.bundle_service import BundleService
from dependency.service.events_service import EventsService
from dependency.service.profile_service import ProfileService

router = APIRouter()
settings: DependencySettings = DependencySettings.load()

profile_service = ProfileService(settings)
bundle_service = BundleService(settings)
events_service = EventsService(settings)
levels_service = LevelsRemoteService(settings)


@router.delete(
    "/profiles/{profile_id}",
    response_class=Response,
    status_code=204,
    responses={
        204: {"model": None, "description": "Profile deleted successfuly"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
        409: {"model": StatusModel, "description": "Conflict. Profile can not be deleted"},
    },
    tags=["profiles"],
    summary="Deletes a profile",
)
async def delete_profiles_x(
        pr: ProfileResource = Permission(ACTION_DELETE_PROFILE, ProfileResource),
        profile_id: str = Path(default=None, required=True, title="id of profile",
                               description="The id of the profile to delete", ),
):
    """Deletes a profile"""

    profile_service.delete_profile(profile_id)


@router.get(
    "/profiles",
    response_model=PageModel[ProfileModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": PageModel[ProfileModel], "description": "Paginated profile list returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["profiles"],
    summary="Retrieves a paginated and optionally filtered list of existing profiles",
)
async def get_profiles(
        req: Request,
        ppr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
        p: int = Query(default=1, title="page number", description="The page number to return. First page is 1.", ge=1,
                       example=1),
        ps: int = Query(default=settings.DEFAULT_PAGE_SIZE, description="The mumber of elements per page.", ge=10,
                        example=10),
        q: str = Query(None, title="term to filter", description="The term for filtering profile names", example=""),
) -> PageModel[ProfileModel]:
    """Retrieves a paginated and optionally filtered list of existing profiles"""
    ...
    items, total = profile_service.list_profiles(p, ps, q)
    
    return PageModel.build(req, items, total, p, ps, q)


@router.get(
    "/profiles/{profile_id}",
    response_model=ProfileModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": ProfileModel, "description": "Profile returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Gets basic properties of a profile",
)
async def get_profiles_x(
        pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
        profile_id: str = Path(default=None, required=True, title="id of profile",
                               description="The id of the profile to retrieve", example="profile_tgderrq"),
) -> ProfileModel:
    """Retrieves the basic properties of a profile."""
    ...

    profile = profile_service.get_profile(profile_id)

    return profile


@router.get(
    "/profiles/{profile_id}/all",
    response_model=List[str],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": List[str], "description": "List of package with versions as strings usable by rez-env"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Retrieves the calculated list of all used package-version (in bundles and standalones) at the level of a profile",
)
async def get_profiles_x_all_packages(
        pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
        profile_id: str = Path(default=None, required=True, title="id of profile",
                               description="The id of the profile from where to calculate the effective package list",
                               example="profile_fgdrew"),
) -> List[str]:
    """Retrieves the calculated list of all used package-version (in bundles and standalones) at the level of a profile"""
    ...
    profile = profile_service.get_effective_profile(profile_id, exclude_deletions=True)

    list: List[str] = []

    for p in profile.packages or []:
        list.append(f"{p.name}-{p.version}")

    for b in profile.bundles or []:
        for p in b.packages or []:
            list.append(f"{p.name}-{p.version}")

    return list

@router.get(
    "/profiles/{profile_id}/packages",
    response_model=List[PackageReferenceModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": List[PackageReferenceModel], "description": "List of package references returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Retrieves the calculated list of packages references at the level of a profile",
)
async def get_profiles_x_packages(
        pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
        profile_id: str = Path(default=None, required=True, title="id of profile",
                               description="The id of the profile from where to calculate the effective package list",
                               example="profile_fgdrew"),
) -> List[PackageReferenceModel]:
    """Retrieves the calculated list of packages references at the level of a profile"""
    ...
    profile = profile_service.get_effective_profile(profile_id, exclude_deletions=True)

    return profile.packages or []


@router.delete(
    "/profiles/{profile_id}/packages/{package_name}",
    status_code=204,
    response_class=Response,
    responses={
        204: {"description": "Package successfully removed at the profile level"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Deletes a package reference at the level of a profile",
)
async def delete_profiles_x_packages_x(
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(title="id of profile",
                               description="The id of profile from where to remove the package reference"),
        package_name: str = Path(title="package name", description="The name of the package in the reference"),
) -> None:
    """Deletes a package at the level of a profile."""

    profile_service.delete_profile_package(profile_id, package_name)


@router.get(
    "/profiles/{profile_id}/bundles",
    response_model=PageModel[BundleModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": PageModel[BundleModel], "description": "List of bundles returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Retrieves the calculated list of bundles at the level of a profile",
)
async def get_profiles_x_bundles(
        req: Request,
        pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),        
        profile_id: str = Path(required=True, default=None, title="id of profile",
                               description="The id of the profile from where to calculate the effective bundle",
                               example="profile_fpazxd"),
        p: int = Query(default=1, title="page number", description="The page number to return. First page is 1.", ge=1,
                       example=1),
        ps: int = Query(default=settings.DEFAULT_PAGE_SIZE, description="The mumber of elements per page.", ge=10,
                        example=10),
) -> PageModel[BundleModel]:
    """Retrieves the paginated, calculated list of bundles at the level of a profile"""
    ...
    profile = profile_service.get_effective_profile(profile_id, exclude_deletions=True)

    bundles: List[BundleModel] = profile.bundles or []

    bundles.sort(key=attrgetter("name"))

    return PageModel.build(req=req, items=bundles, p=p, ps=ps, q=None, total=len(bundles), items_pre_paged=False)


@router.post(
    "/profiles/{profile_id}/bundles/{bundle_name}",
    status_code=201,
    response_model=BundleModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        201: {"model": BundleModel, "description": "Successful request"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Add a profile bundle",
)
async def post_profiles_x_bundles_x(
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(description="id of profile"),
        bundle_name: str = Path(description="name of bundle in library"),
) -> Optional[BundleModel]:
    """Add a bundle to a profile using the name of a previously know bundle already in the bundles library"""
    ...
    bundle = bundle_service.get_bundle(bundle_name)

    return profile_service.add_profile_bundle(profile_id, bundle.name, bundle.description, bundle.packages)


@router.delete(
    "/profiles/{profile_id}/bundles/{bundle_name}",
    status_code=204,
    response_class=Response,
    responses={
        204: {"description": "Bundle deleted successfuly from profile"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Deletes a bundle from a profile",
)
async def delete_profiles_x_bundles_x(
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(description="id of profile"),
        bundle_name: str = Path(description="name of bundle"),
) -> None:
    """Deletes a bundle from a profile"""

    profile_service.delete_profile_bundle(profile_id, bundle_name)

    return None


@router.post(
    "/profiles/{profile_id}/validate",
    status_code=204,
    response_class=Response,
    responses={
        204: {"description": "Profile validation event triggered"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Request a validation process for a profile ",
)
async def post_profiles_x_validate(
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(description="id of profile"),
) -> None:
    """Requests a profile to be validated"""

    e_profile = profile_service.get_effective_profile(profile_id=profile_id)

    if e_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    events_service.on_profile_validate(e_profile)

    return None


@router.put(
    "/on-validity-change",
    status_code=204,
    response_class=Response,
    responses={
        204: {"description": "Validity status changed successfully"},
        422: {"model": StatusModel, "description": "Unable to process"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Declares a profile as valid or invalid",
)
async def put_on_validity_change(
        validity_event: ProfileValidityEvent = Body(
            None, description="The payload of event to change a validity status for a profile"
        ),
) -> None:
    """Receive events with changes to the validity of profiles"""

    if validity_event is None:
        raise HTTPException(status_code=400, detail="Bad request. Empty body.")

    log.debug(f"INCOMING EVENT: {json.dumps(validity_event.dict())}")

    validity_status = validity_event.detail

    profile_service.change_profile_status(
        validity_status.id,
        PROFILE_STATUS_VALID
        if validity_status.validation_result.lower() == "valid"
        else PROFILE_STATUS_INVALID,
        validity_status.result_reason,
        validity_status.rxt
    )


@router.patch(
    "/profiles/{profile_id}",
    response_model=ProfileModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": ProfileModel, "description": "Profile patched successfully"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Update basic properties of a profile",
)
async def patch_profiles_x(
        req: Request,
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        user: User = Depends(AuthManager.from_token),
        profile_id: str = Path(None, description="id of profile"),
        patch: PatchProfileModel = Body(
            None, description="The payload to patch a profile"
        ),
) -> ProfileModel:
    """Update basic properties of a profile

    In case the path is being changed then a new profile (different id) will be created at target path
    and the old profile will be removed.    
    """
    ...
    profile = profile_service.get_profile(profile_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")    

    # service level patch allows changing path by creating new profile_id and returning new profile, deleting the old one
    patched: ProfileModel = profile_service.patch_profile(profile_id, patch, user) 

    return patched


@router.post(
    "/profiles/{profile_id}/comments",
    status_code=201,
    response_model=ProfileCommentModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        201: {
            "model": ProfileCommentModel,
            "description": "Profile comment created successfully",
        },
        400: {"model": StatusModel, "description": "Bad request"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Add a profile comment",
)
async def post_profiles_x_comments(
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(None, description="id of profile"),
        new_profile_comment: NewProfileCommentModel = Body(
            None, description="The payload to add a profile comment"
        ),
) -> ProfileCommentModel:
    """Add a profile comment"""
    ...

    if new_profile_comment is None:
        raise HTTPException(status_code=400, detail="Body missing")

    profile = profile_service.get_profile(profile_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    new_profile_comment.created_by = "system"

    return profile_service.add_profile_comment(profile_id, new_profile_comment)


@router.get(
    "/profiles/{profile_id}/comments",
    response_model=PageModel[ProfileCommentModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        200: {"model": PageModel[ProfileCommentModel], "description": "Successful operation"},
        400: {"model": StatusModel, "description": "Bad request"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="List profile comments",
)
async def get_profiles_x_comments(
        req: Request,
        pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
        profile_id: str = Path(description="id of profile"),
        p: int = Query(1, description="page number to return. First page is 1.", ge=1),
        ps: int = Query(
            settings.DEFAULT_PAGE_SIZE, description="Number of elements per page.", ge=10
        ),
) -> PageModel[ProfileCommentModel]:
    """Retrieves the list of profile comments. This endpoint paginates results"""
    ...

    profile = profile_service.get_profile(profile_id)

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    comments, total = profile_service.list_profile_comments(profile_id, p, ps)

    if comments is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return PageModel[ProfileCommentModel].build(req, comments, total, p, ps, None)


@router.post(
    "/profiles",
    response_model=ProfileModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"model": ProfileModel, "description": "Profile created successfully"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["profiles"],
    summary="Create a new profile attaching it to a level",
)
async def post_profiles(
    # req: Request,
    pr: ProfileResource = Permission(ACTION_CREATE_PROFILE, ProfileResource),
    user: User = Depends(AuthManager.from_token),
    new_profile: NewProfileModel = Body(default=None, required=True, title="new profile payload", description="The payload to create a new profile"),
    path: str = Query(
        required=True,
        title="profile level path",
        description="The path to the level where the profile will be attached to"
    ),
) -> Optional[ProfileModel]:
    """Creates a new profile attaching it to a level. The profile is initially created with no packages, bundles or comments"""
    ...
    # log.debug(f"Permissions: {ilr}")
    # token: Optional[str] = req.headers.get("Authorization", None)
    return profile_service.create_profile(LevelPath.canonize(path), new_profile, operator=user)


# @router.delete(
#     "/effective-profile",
#     response_model=List[ProfileModel],
#     response_model_exclude_defaults=False,
#     response_model_exclude_none=True,
#     response_model_exclude_unset=True,
#     status_code=200,
#     responses={
#         200: {"model": ProfileModel, "description": "Deattached successfully"},
#         401: {"model": StatusModel, "description": "Unauthenticated"},
#         403: {"model": StatusModel, "description": "Unauthorized"},
#         404: {"model": StatusModel, "description": "Profile not found"},
#     },
#     tags=["levels"],
#     summary="Deattaches profiles from a level path by deleting them",
# )
# async def delete_profile(    
#     path: str = Query(        
#         description="Path to detach from"
#     ),
#pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
# ) -> List[ProfileModel]:
#     """Detaches profiles from a level path by deleting them"""
#     ...
#     return profile_service.detach_from_path(LevelPath.canonize(path))

@router.get(
    "/effective-profile",
    response_model=FullProfileModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"model": FullProfileModel, "description": "Profile calculated and returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["profiles"],
    summary="Retrieves the effective profile at a level",
)
async def get_effective_profile(
    path: str = Query(title="level path", default="/", example="/toronto",
        description="The path of the level where the effective profile is to be calculated"
    ),
    pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
) -> Optional[FullProfileModel]:
    """Retrieves the effective profile, calculated at a level"""
    ...
    p = profile_service.get_effective_profile_by_path(LevelPath.canonize(path), exclude_deletions=True)

    if p is None:
        raise HTTPException(status_code=404, detail="Unable to calculate effective profile, root profile may be empty")

    return p

@router.get(
    "/effective-profile/all",
    response_model=List[str],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"model": List[str], "description": "Packages of profile returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Retrieves all the effective packages at a path",
)
async def get_all_effective_profile_packages(    
    pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
    path: str = Query(default="/", required="False", title="level path", example="/toronto/Project51",
        description="The path of the level where the effective profile packages are to be calculated"
    ),
) -> Optional[List[str]]:
    """Retrieves all the effective profile packages, calculated at a level path"""
    ...
    profile = profile_service.get_effective_profile_by_path(LevelPath.canonize(path), exclude_deletions=True)

    if profile is None:
        raise HTTPException(status_code=404, detail="Unable to calculate the effective profile, root profile may be empty")
    
    list: List[str] = []

    for p in profile.packages or []:
        list.append(f"{p.name}-{p.version}")

    for b in profile.bundles or []:
        for p in b.packages or []:
            list.append(f"{p.name}-{p.version}")

    return list

@router.get(
    "/effective-profile/packages",
    response_model=List[PackageReferenceModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"model": List[PackageReferenceModel], "description": "Packages of profile returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["profiles"],
    summary="Retrieves the effective profile packages at a level",
)
async def get_effective_profile_packages(    
    pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
    path: str = Query(default="/", required="False", title="level path", example="/toronto/Project51",
        description="The path of the level where the effective profile packages are to be calculated"
    ),
) -> Optional[List[PackageReferenceModel]]:
    """Retrieves the effective profile packages, calculated at a level"""
    ...
    p = profile_service.get_effective_profile_by_path(LevelPath.canonize(path), exclude_deletions=True)

    if p is None:
        raise HTTPException(status_code=404, detail="Unable to calculate the effective profile, root profile may be empty")

    return p.packages

@router.get(
    "/effective-profile/bundles",
    response_model=List[BundleModel],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        200: {"model": List[BundleModel], "description": "Bundles of profile returned"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["profiles"],
    summary="Retrieves the effective profile bundles at a level",
)
async def get_effective_profile_bundles(    
    pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
    path: str = Query(     
        required=False,
        default="/",
        title="level path",
        example="/mumbai/Project1",
        description="The path of the level where the effective profile bundles are to be calculated"
    ),
) -> Optional[List[BundleModel]]:
    """Calculates the effective profile bundles at a path"""
    ...
    p = profile_service.get_effective_profile_by_path(LevelPath.canonize(path), exclude_deletions=True)

    if p is None:
        raise HTTPException(status_code=404, detail="Unable to calculate effective profile, root profile may be empty")

    return p.bundles

def _build_xml_package_block(packages : List[PackageReferenceModel], margin : str) -> str: 
    xml_packages = ""
    for p in packages:
        xml_packages = xml_packages + margin + "<package name=\"" + str(p.name) + "\"" +  " \"version\"=\"" + str(p.version) + "\" />\n"
    return "\n" + margin + xml_packages.strip() if len(packages) > 0 else ""

@router.get(
    "/effective-profile/xml",
    status_code=200,
    responses={
        200: {"model": StatusModel, "description": "Returned sucessfully"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
    },
    tags=["profiles"],
    summary="Returns the effective profile for a level, represented as XML",
)
async def get_effective_profile_xml(
    pr: ProfileResource = Permission(ACTION_VIEW_PROFILE, ProfileResource),
    path: str = Query(
        default="/",
        example="/",
        title="level path",        
        description="The path to the level where the effective profile is to be calculated"
    ),
) -> Any:
    """Returns a profile xml representation for an specified level path"""
    ...

    path = LevelPath.canonize(path)

    profile = profile_service.get_effective_profile_by_path(path, exclude_deletions=True)

    if profile is None:
        raise HTTPException(status_code=404, detail="Unable to calculate effective profile")
    
    p_margin : str = "        "

    xml_packages : str = _build_xml_package_block(profile.packages, p_margin)

    xml_bundles : str = ""
    for b in profile.bundles:
        xml_bundles = xml_bundles + "\n" + p_margin + "<bundle name=\"" + str(b.name) + "\">" + _build_xml_package_block(b.packages, p_margin + p_margin) + "\n" + p_margin + "</bundle>\n"

    data = f"""<?xml version="1.0"?>

<package_configuration version="1">

    <profile name=""> <!-- effective profile at path '{path}' -->
        {xml_packages}
        {xml_bundles}
    </profile>

</package_configuration>
    """
    return Response(content=data, media_type="application/xml")

@router.post(
    "/effective-profile/xml",
    response_model=ImportReport,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=False,
    status_code=201,
    responses={
        200: {"model": ImportReport, "description": "Profile not imported, issues found, summary returned"},
        201: {"model": ImportReport, "description": "Profile imported into path"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        409: {"model": StatusModel, "description": "Conflict"},
        422: {"model": StatusModel, "description": "Provided data can't be processed"},
    },
    tags=["profiles"],
    summary="Import a profile represented as XML file into level identified by its path",
)
async def post_effective_profile_xml(
    file: UploadFile,
    pr: ProfileResource = Permission(ACTION_CREATE_PROFILE, ProfileResource),
    user: User = Depends(AuthManager.from_token),
    path: str = Query(
        default="/",
        example="/mumbai/Projects-101",
        title="level path",
        description="The path to the level where the imported profile will be attached to"
    ),
    strict: bool = Query(
        default=False,
        required=False,
        title="strict checks",
        description="True to only import if no issues are found, False otherwise",
        example=False
    ),
) -> ImportReport:
    """Import a profile from its xml representation into a specified level path"""
    ...
    if file.content_type != "application/xml":
        raise HTTPException(status_code=400, detail="invalid file content type")

    xml = await file.read()

    # TODO: properly validate path syntax and existence
    # TODO: if path is right under root (children of /), then validate is a known site label

    import_report = profile_service.import_profile(path=LevelPath.canonize(path), xml=xml, replace=False, strict=strict, operator_user=user)

    return import_report

@router.put(
    "/effective-profile/xml",
    response_model=ImportReport,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        200: {"model": ImportReport, "description": "Profile not imported, issues found, summary returned"},
        201: {"model": ImportReport, "description": "Profile imported into path replacing previous"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        409: {"model": StatusModel, "description": "Conflict"},
        422: {"model": StatusModel, "description": "Provided data can't be processed"},
    },
    tags=["profiles"],
    summary="Import a profile represented as XML file into level identified by its path, replacing the current one",
)
async def put_effective_profile_xml(
    file: UploadFile,
    pr: ProfileResource = Permission(ACTION_UPDATE_PROFILE, ProfileResource),
    user: User = Depends(AuthManager.from_token),
    path: str = Query(
        default="/",
        description="Path where the imported profile will be replacing the existing one"
        "Default value: /",
    ),
    strict: bool = Query(
        default=False,
        description="True to only import if no issues are found, False otherwise"
        "Default value: False",
    ),
) -> ImportReport:
    """Import a profile from its xml representation into a specified level path, to replace the existing"""
    ...
    if file.content_type != "application/xml":
        raise HTTPException(status_code=400, detail="invalid file content type")

    xml = await file.read()

    import_report = profile_service.import_profile(operator_user=user, path=LevelPath.canonize(path), xml=xml, replace=True, strict=strict)
    
    return import_report
    