## coding: utf-8
from typing import Set, Dict

from fastapi import (
    APIRouter,
    Depends
)

from common.service.permissions_service import PermissionService, matrix  # type: ignore
from common.api.model.status_model import StatusModel
from common.domain.user import User
from common.auth.auth_manager import AuthManager
from dependency.dependency_settings import DependencySettings

router = APIRouter()
settings: DependencySettings = DependencySettings.load()

permission_service = PermissionService()


@router.get(
    "/permissions",
    responses={
        200: {"model": Set[str], "description": "Listing all permissions for the current user"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"}
    },
    tags=["permissions"],
    summary="List permissions for current user",
    response_model=Set[str],
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True
)
async def list_permissions(
        user: User = Depends(AuthManager.from_token)
) -> Set[str]:
    """Retrieves the list of permissions for the current user. """
    ...
    permissions = permission_service.get_user_permissions(user)
    return permissions


@router.get(
    "/perm-matrix",
    responses={
        200: {"model": Dict, "description": "The matrix of permissions"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"}
    },
    tags=["permissions"],
    summary="The permissions matrix",
    response_model=Dict,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True
)
async def get_perm_matrix(
        user: User = Depends(AuthManager.from_token)
) -> Set[str]:
    """Retrieves current permission matrix. """
    ...
    return matrix()  # type: ignore
