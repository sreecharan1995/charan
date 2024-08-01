
from typing import Dict, List, Optional

from fastapi import (APIRouter, Body, Depends, HTTPException, Path, Query,
                     Request, Response)
from fastapi.routing import APIRouter

from common.api.model.page_model import PageModel
from common.api.model.status_model import StatusModel
from common.api.utils import Utils as ApiUtils
from common.auth.auth_manager import AuthManager, Permission
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.status_exception import StatusException
from common.domain.user import User
from common.logger import log
from configs.api.auth.config_resource import (ACTION_CREATE_CONFIG,
                                              ACTION_DELETE_CONFIG,
                                              ACTION_UPDATE_CONFIG,
                                              ACTION_VIEW_CONFIG,
                                              ConfigResource)
from configs.api.model.compact_config_model import CompactConfigModel
from configs.api.model.config_model import ConfigModel
from configs.api.model.config_status_model import ConfigStatusModel
from configs.api.model.create_config_model import CreateConfigModel
from configs.api.model.patch_config_model import PatchConfigModel
from configs.configs_settings import ConfigsSettings
from configs.domain.config_item import ConfigItem

router = APIRouter()

from configs.service.configs_service import ConfigsService

configs_settings = ConfigsSettings.load_configs()
configs_service: ConfigsService = ConfigsService(configs_settings)

@router.post(
    "/configs",
    responses={
        200: {"model": ConfigModel, "description": "Config returned"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Creates a config",
    response_model=ConfigModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
)
async def post_configs(    
    req: Request,    
    br: ConfigResource = Permission(ACTION_CREATE_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    inherit: bool = Query(
            required=False, default=True, description="true will use inheritance to detect and avoid setting config keys if matching values are already in parents"
        ),        
    create_config_model: CreateConfigModel = Body(
            None, description="The config to create"
        ),
    ) -> ConfigModel:
    """Creates a config and returns it
    
    A configuration is always created inactive and attached to a level. There can be multiple configuration with the same name in the same level, but only one of them 
    is the current active one.
    """
    ...
    
    if create_config_model is None:
        raise HTTPException(status_code=400, detail="Missing body")

    config_model: Optional[ConfigModel] = None

    try:        
        config_model = configs_service.create_config(create_config_model=create_config_model, operator_user=user, inherit=inherit if inherit is not None else True)
    except StatusException as se:
        log.error(f"Error while creating configuration: {se}")
        raise HTTPException(status_code=se.code, detail=se.message)
    except BaseException as e:
        log.error(f"Error while creating configuration: {e}")

    if config_model is None:
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")
    
    return config_model

@router.get(
    "/configs/{id}",
    responses={
        200: {"model": ConfigModel, "description": "Config returned"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Returns a config",
    response_model=ConfigModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
)
async def get_configs_x(    
    req: Request,    
    br: ConfigResource = Permission(ACTION_VIEW_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    id: str = Path(
            required=True, description="The id of the config to retrieve"
        ),
    resolve: bool = Query(
            required=False, default=True, description="true will perform token replacement, false will not"
        ),        
    ) -> ConfigModel:
    """Returns an existing configuration using its id.
    
    The json configuration returned with this endpoint is not the "effective" current/non-current configuration, but the partial set of properties stored 
    in its level node. So there are no inherited keys from configurations in levels above.
    """

    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id") 

    config_model: Optional[ConfigModel] = None

    token_dict: Dict[str,str] = ApiUtils.extract_dict_from_query_params(req)
    
    try:        
        config_model = configs_service.get_config(id=id, operator_user=user, token_dict=token_dict if resolve else None)
    except BaseException as e:
        log.error(f"Error while retrieving or resolving tokens for configuration: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if config_model is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config_model

@router.get(
    "/configs/current/{name}",
    responses={
        200: {"model": ConfigModel, "description": "Effective config returned"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Returns the effective config",
    response_model=ConfigModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_configs_current_x(    
    req: Request,    
    br: ConfigResource = Permission(ACTION_VIEW_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    name: str = Path(
            required=True, description="The name of the config to use"
        ),
    path: str = Query(
            required=True, description="The level path from where to calculate the effective config"
        ),        
    resolve: bool = Query(
            required=False, default=True, description="true will perform token replacement, false will not"
        ),        
    inherit: bool = Query(
            required=False, default=True, description="true will use inheritable parents, false will stop inheritance on first parent found"
        ),        
    ) -> ConfigModel:
    """Returns an effective configuration using its name and a path, optionally replacing tokens
    
    The json configuration returned will inherit or not (according to the inherit query paramenter) the keys from configs considered current and 
    matching the same name from levels above.
    """
    ...

    if not ConfigItem.is_name_valid(name):
        raise HTTPException(status_code=400, detail="provided name is not acceptable as a config name")

    if not ParsedLevelPath.is_path_acceptable(path):
        raise HTTPException(status_code=400, detail="provided path is not acceptable as a level path")
    
    config_model: Optional[ConfigModel] 

    token_dict: Dict[str,str] = ApiUtils.extract_dict_from_query_params(req)
    
    try:        
        config_model = configs_service.get_effective_config(name=name, level_path=path, operator_user=user, token_dict=token_dict if resolve else None, inherit=inherit if inherit is not None else True)
    except BaseException as e:
        log.error(f"Error while retrieving or tokenizing effective configuration: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if config_model is None:
        raise HTTPException(status_code=404, detail="No effective configuration available")
    
    return config_model


@router.get(
    "/configs/{id}/current",
    responses={
        200: {"model": ConfigModel, "description": "Preview of effective config returned"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Returns a preview of the effective config",
    response_model=ConfigModel,
    response_model_exclude_unset=True,
    response_model_exclude_none=False,
)
async def get_configs_x_current(    
    req: Request,    
    br: ConfigResource = Permission(ACTION_VIEW_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    id: str = Path(
            required=True, description="The id of the config to get preview from"
        ),
    resolve: bool = Query(
            required=False, default=True, description="true will perform token replacement, false will not"
        ),        
    inherit: bool = Query(
            required=False, default=None, description="true will use inheritable parents, false will stop inheritance on first parent found"
        ),        
    ) -> ConfigModel:
    """Returns an effective configuration considering the specified id as the deepest level node, disregarding its current or non-current status, and optionally replacing tokens

    The json configuration returned will inherit or not (according to the inherit query paramenter) the keys from configs considered current and 
    matching the same name from levels above. 
    """
    ...

    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id")

    token_dict: Dict[str,str] = ApiUtils.extract_dict_from_query_params(req)

    try:        
        effective_config_model = configs_service.get_effective_config_preview(id=id, operator_user=user, token_dict=token_dict if resolve else None, inherit=inherit)
    except BaseException as e:
        log.error(f"Error while retrieving or tokenizing effective configuration preview: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if effective_config_model is None:
        raise HTTPException(status_code=404, detail="No effective configuration preview available")
    
    return effective_config_model

@router.get(
    "/configs",
    responses={
        200: {"model": PageModel[CompactConfigModel], "description": "Configs page returned"},
        400: {"model": StatusModel, "description": "Bad usage"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Returns a paginated and optionally filtered list of configs",
    response_model=PageModel[CompactConfigModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_configs(
    req: Request,    
    br: ConfigResource = Permission(ACTION_VIEW_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    name: str = Query(
            required=False, default=None, description="The exact name of configs to retrieve, or subtring match if ~ is suffixed to parameter."
        ),
    path: str = Query(
            required=False, default=None, description="The level path of configs to retrieve"
        ),        
    p: int = Query(default=1, title="page number", description="The page number to return. First page is 1.", ge=1, example=1),
    ps: int = Query(default=configs_settings.DEFAULT_PAGE_SIZE, title="page size", description="The number of elements per page.", ge=10, example=10),
    ) -> PageModel[CompactConfigModel]:
    """Returns a paginated and optionally filtered list of configs
    
    The configs returned are a simplified view suited for listing which doesn't include the json configuration keys.
    """
    ...

    if name is not None and not ConfigItem.is_name_valid(name, True):
        raise HTTPException(status_code=400, detail="provided name is not acceptable as a config name")

    if path is not None and not ParsedLevelPath.is_path_acceptable(path):
        raise HTTPException(status_code=400, detail="provided path is not acceptable as a level path")

    configs: Optional[List[CompactConfigModel]] = None
    total: int

    try:
        configs, total = configs_service.find_configs(operator_user=user, name=name, path=path, page_number=p, page_size=ps)
    except BaseException as e:
        log.error(f"Error while retrieving configurations: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if configs is None:
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")
    
    return PageModel.build(req=req, items=configs, total=total, p=p, ps=ps, q=None)


@router.delete(
    "/configs/{id}",
    status_code=204,
    response_class=Response,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        204: {"model": None, "description": "Config deleted successfuly."},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Deletes a config",
)
async def delete_configs_x(
    br: ConfigResource = Permission(ACTION_DELETE_CONFIG, ConfigResource),
    user: User = Depends(AuthManager.from_token),
    id: str = Path(
            required=True, description="The id of the config to delete"
        )
):
    """Deletes a config using its id
    
    Only inactive (non-current) configurations can be deleted.
    """

    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id") 

    success: Optional[bool]

    try:       
         success = configs_service.delete_config(operator_user=user, id=id)
    except StatusException as se:
        raise HTTPException(status_code=se.code, detail=se.message)
    except BaseException as e:
        log.error(f"Error while deleting configuration: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if success is None or not success:
            raise HTTPException(status_code=404, detail="Configuration not found")    


@router.patch(
    "/configs/{id}",
    response_model=ConfigModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=False,
    response_model_exclude_unset=True,
    responses={
        200: {"model": ConfigModel, "description": "Config patched successfully"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Patch a config",
)
async def patch_configs_x(
        req: Request,
        pr: ConfigResource = Permission(ACTION_UPDATE_CONFIG, ConfigResource),
        user: User = Depends(AuthManager.from_token),
        id: str = Path(None, description="id of config"),
        inherit: bool = Query(
            required=False, default=True, description="true will use inheritance to detect and avoid setting config keys if matching values are already in parents"
        ),        
        patch: PatchConfigModel = Body(
            None, description="The payload to patch a config"
        ),
) -> ConfigModel:
    """Patch some of the properties of a config

    Only inactive (non-current) configurations can be patched. A configuration name and level can be changed too, but in this case notice that the effective 
    json keys may substantially differ from what you expect because keys will be inherited from new parents.
    """
    ...
    
    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id") 

    config_model: Optional[ConfigModel] = None

    try:
        config_model = configs_service.patch_config(id=id, operator_user=user, patch=patch, inherit=inherit if inherit is not None else True)
    except StatusException as se:
        log.error(f"Error while retrieving configuration: {se}")
        raise HTTPException(status_code=se.code, detail=se.message)
    except BaseException as e:
        log.error(f"Error while retrieving configuration: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if config_model is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config_model

@router.put(
    "/configs/{id}/status",    
    status_code=200,
    response_model=None,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={        
        200: {"model": None, "description": "Successfully updated config status"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Sets the current/non-current status for a config",
)
async def put_configs_x_status(
        req: Request,
        pr: ConfigResource = Permission(ACTION_UPDATE_CONFIG, ConfigResource),
        user: User = Depends(AuthManager.from_token),
        id: str = Path(None, description="id of config"),
        status_model: ConfigStatusModel = Body(
            None, description="The payload to set the current/non-current status for a config"
        ),
) -> None:
    """Sets the current or non-current status for a config.

    Altought multiple configs with the same name can be present in a level, only one of them is considered current active one. When a configuration is activated via this endpoint, all other configs with
    the same name in the same level will be considered non current (they get inactivated). When a configuration is inactivated via this endpoint, then it may be the case that there are no active 
    configurations for its name in the level.
    """
    ...
    
    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id") 

    success: Optional[bool]

    try:
        success = configs_service.set_config_status(id=id, operator_user=user, status_model=status_model)
    except BaseException as e:
        log.error(f"Error while setting configuration status: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if success is None:
        raise HTTPException(status_code=404, detail="Configuration not found")    

@router.get(
    "/configs/{id}/status",    
    response_model=ConfigStatusModel,
    response_model_exclude_defaults=False,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={        
        200: {"model": None, "description": "Returned config status"},
        401: {"model": StatusModel, "description": "Unauthenticated"},
        403: {"model": StatusModel, "description": "Unauthorized"},
        404: {"model": StatusModel, "description": "Not found"},
    },
    tags=["configs"],
    summary="Returns the status for a config using its id",
)
async def get_configs_x_status(
        req: Request,
        pr: ConfigResource = Permission(ACTION_VIEW_CONFIG, ConfigResource),
        user: User = Depends(AuthManager.from_token),
        id: str = Path(None, description="id of config"),        
) -> ConfigStatusModel:
    """Gets the current or non-current status for a config

    Only one configuration is the current active one for a name and level combination, all others matching are considered non-current (inactive)
    """
    ...
    
    if not ConfigItem.is_id_valid(id):
        raise HTTPException(status_code=400, detail="provided id is not acceptable as a config id") 

    status_model: Optional[ConfigStatusModel]

    try:
        status_model = configs_service.get_config_status(id=id, operator_user=user)
    except BaseException as e:
        log.error(f"Error while getting configuration status: {e}")
        raise HTTPException(status_code=503, detail="A temporary problem prevents servicing")

    if status_model is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return status_model
