import copy
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonpickle  # type: ignore

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.status_exception import StatusException
from common.domain.user import User
from common.logger import log
from common.service.levels_remote_service import LevelsRemoteService
from configs.api.model.compact_config_model import CompactConfigModel
from configs.api.model.config_model import ConfigModel
from configs.api.model.config_status_model import ConfigStatusModel
from configs.api.model.create_config_model import CreateConfigModel
from configs.api.model.patch_config_model import PatchConfigModel
from configs.configs_settings import ConfigsSettings
from configs.domain.config_item import ConfigItem
from configs.service.aws.configs_ddb import ConfigsDdb

TOKEN_DELIMITER: str = "([^<])?<(\\w+?)>([^>])?"

class ConfigsService:
    """Provides the methods and login to store, recover, perform token-replacements and validate operations when creating, editing o accessing configs.
    """

    _configs_settings: ConfigsSettings
    _configs_ddb: ConfigsDdb
    _levels_remote_service: LevelsRemoteService

    def __init__(self, settings: ConfigsSettings):
        self._configs_settings = settings
        self._configs_ddb = ConfigsDdb(settings=settings)
        self._levels_remote_service = LevelsRemoteService(settings=settings)

    def create_config(
            self, operator_user: User,
            create_config_model: CreateConfigModel,
            inherit: bool = True) -> Optional[ConfigModel]:

        level_path = LevelPathModel.to_level_path(create_config_model.level)
        parsed_level_path: Optional[
            ParsedLevelPath] = ParsedLevelPath.from_level_path(level_path)

        if parsed_level_path is None:
            log.warning(
                f"Unable to create configuration for name '{create_config_model.name}'. Level parse failed: '{level_path.get_path()}'"
            )
            return None

        path = parsed_level_path.to_level_path().get_path()

        if not self._levels_remote_service.is_visible(path, token=operator_user.token, check_existence=True):
            log.debug(f"creating config: config level '{path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None        

        effective_config_model: Optional[ConfigModel]
        simplified_config_json: Dict[str,Any] = create_config_model.configuration        
        
        if inherit and create_config_model.configuration is not None: # reduce config keys
            # calculate effective config to attempt reducing the patch configuration to the minimum required by taking into consideration 
            # inherited matching values from parents

            try:                
                effective_config_model = self.get_effective_config(name=create_config_model.name, level_path=path, operator_user=operator_user, token_dict=None, inherit=True)
            except BaseException as e:
                log.error(f"Error while internally retrieving effective configuration: {e}")
                raise StatusException(code=503, message="A temporary problem prevents servicing")

            if effective_config_model is not None:
                simplified_config_json = self._reduced_configuration(create_config_model.configuration, effective_config_model.configuration)                        

        config_item: Optional[ConfigItem] = self._configs_ddb.create_config(
            path=path,
            name=create_config_model.name,
            description=create_config_model.description,
            inherits=create_config_model.inherits,
            created_by=operator_user.username)

        if config_item is None:
            log.warning(
                f"Unable to create configuration for name '{create_config_model.name}' at path '{level_path.get_path()}'"
            )
            return None

        if not self._write_json_config(config_item.id,
                                       simplified_config_json):
            log.warning(
                f"Unable to create configuration data file for name '{create_config_model.name}' at path '{level_path.get_path()}'"
            )
            return None

        config_json: Optional[Dict[str, Any]] = self._load_json_config(
            config_item.id, None)

        if config_json is None:
            log.warning(
                f"Unable to read configuration data file for name '{create_config_model.name}' at path '{level_path.get_path()}'"
            )
            return None

        return ConfigModel.from_config_item_and_json(config_item, config_json)

    def patch_config(self, operator_user: User, id: str,
                     patch: PatchConfigModel, inherit: bool = True) -> Optional[ConfigModel]:
        
        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(
            id)

        if config_item is None:
            log.debug(
                f"patching config: unable to find configuration with id '{id}', operator '{operator_user.username}'"
            )
            return None

        # check user has access to original path
        if not self._levels_remote_service.is_visible(config_item.path, token=operator_user.token, check_existence=False):
            log.debug(f"patching config: config level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None
        
        if config_item.active > 0:
                log.debug(
                    f"Unable to patch configuration with id '{id}', operator '{operator_user.username}': can't modify an active configuration'"
                )
                raise StatusException(code=409, message="Configuration is active, can't modify it")

        patch_level: Optional[
            ParsedLevelPath] = ParsedLevelPath.from_level_path(
                patch.level.to_level_path(
                )) if patch is not None and patch.level is not None else None

        patched_path: str = patch_level.to_level_path().get_path(
        ) if patch_level is not None else config_item.path
        patched_name: str = patch.name if patch is not None and patch.name is not None else config_item.name
        patched_description: str = patch.description if patch is not None and patch.description is not None else config_item.description
        patched_inherits: bool = patch.inherits if patch is not None and patch.inherits is not None else config_item.inherits

        # if patched_path != config_item.path or patched_name != config_item.name:  # if name or path is changed..
        #     if config_item.active > 0:  # TODO: Impl don't allow moving an active config
        #         log.debug(
        #             f"Unable to patch configuration with id '{id}', operator '{operator_user.username}': can't change name or path for an active config'"
        #         )
        #         raise StatusException(code=409, message="Configuration is active, can't change name or level")
        #     patched_active = 0  # to make sure is kept inactive when moved
        # else:
        #     patched_active = config_item.active  # keep same vale if not moved

        # check user has access to destination path and that destionation exists:
        if not self._levels_remote_service.is_visible(patched_path, token=operator_user.token, check_existence=True):
            log.debug(f"patching config: target level '{patched_path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        effective_config_model_p: Optional[ConfigModel] = None
        effective_config_model_h: Optional[ConfigModel] = None
        simplified_config_json: Optional[Dict[str,Any]] = patch.configuration if patch is not None else None
        
        if inherit and patch is not None and patch.configuration is not None: # reduce patch
            # calculate effective config to attempt reducing the patch configuration to the minimum required by taking into consideration 
            # inherited matching values from parents
            try:
                candidate_config_item = ConfigItem(id=config_item.id, path=patched_path, name=patched_name, description=patched_description, inherits=patched_inherits, active=0, created=config_item.created, updated=config_item.updated, created_by=config_item.created_by)
                effective_config_model_p = self._get_effective_config_item_preview(config_item=candidate_config_item, operator_user=operator_user, token_dict=None, inherit=True, exclude_item=True)
                effective_config_model_h = self._get_effective_config_item_preview(config_item=candidate_config_item, operator_user=operator_user, token_dict=None, inherit=True)        
            except BaseException as e:
                log.error(f"Error while internally retrieving effective configuration preview: {e}")
                raise StatusException(code=503, message="A temporary problem prevents servicing")

            if effective_config_model_p is not None and effective_config_model_h is not None:                
                merged = self._inherited_configuration(parent_config=effective_config_model_h.configuration, child_config=patch.configuration, remove_missing=True)
                simplified_config_json = self._reduced_configuration(base_config=effective_config_model_p.configuration, config=merged)                        
        
        patched_config: Optional[ConfigItem] = self._configs_ddb.patch_config(
            id=id,
            path=patched_path,
            name=patched_name,
            description=patched_description,
            inherits=patched_inherits,
            active=0)

        if patched_config is None:
            log.debug(
                f"Unable to patch configuration with id '{id}', operator '{operator_user.username}'"
            )
            return None

        # if patched_path != config_item.path or patched_name != config_item.name: # if name or path is changed..
        #     if patched_active: # set current if was active or activation was requested
        #         self._configs_ddb.set_current_by_id(id)
        #     else: # if was inactive or requested to be inactive, then set to inactive, so other active continue to be the current
        #         self._configs_ddb.inactivate_config_by_id(id) # not using set_non_current to let other configs as they are
        # else:
        #     if not config_item.active and patched_active: # was not active but need to be active (only active: current)
        #         self._configs_ddb.set_current_by_id(id)
        #     elif config_item.active and not patched_active: # was active but needs to be inactive (all inactive: no current)
        #         self._configs_ddb.set_non_current_by_id(id)

        if simplified_config_json is not None:
            if not self._write_json_config(id, simplified_config_json):
                log.warning(
                    f"Unable to patch configuration data file for id '{id}', operator '{operator_user.username}'"
                )
                return None

        if inherit: # if use parents (not patching the local node config, but the effective one)
            return self.get_effective_config_preview(operator_user=operator_user, id=patched_config.id, token_dict=None, inherit=config_item.inherits) # honour the node inherits policy
        else:
            config_json: Optional[Dict[str, Any]] = self._load_json_config(
                id, None)

            if config_json is None:
                log.warning(
                    f"Unable to read from configuration data file for id '{id}', operator '{operator_user.username}'"
                )
                return None

            return ConfigModel.from_config_item_and_json(patched_config,
                                                        config_json)

    def set_config_status(self, operator_user: User, id: str,
                          status_model: ConfigStatusModel) -> Optional[bool]:

        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(id)

        if config_item is None:
            log.debug(
                f"setting config status: unable to find configuration with id '{id}', operator '{operator_user.username}'"
            )
            return None

        check_existence: bool = status_model.current  # only check existance when trying to set as current, otherwise allow the operation so it can be eventually deleted, etc

        if not self._levels_remote_service.is_visible(config_item.path, token=operator_user.token, check_existence=check_existence):
            log.debug(f"setting config status: level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        if status_model.current:
            patched_config: Optional[
                ConfigItem] = self._configs_ddb.set_current_by_id(id)
        else:
            patched_config: Optional[
                ConfigItem] = self._configs_ddb.set_non_current_by_id(id)

        if patched_config is None:
            log.debug(
                f"Unable to set the status for the configuration with id '{id}', operator '{operator_user.username}'"
            )
            return False

        return True

    def find_configs(
            self, operator_user: User, name: Optional[str],
            path: Optional[str], page_number: int,
            page_size: int) -> Tuple[Optional[List[CompactConfigModel]], int]:
        
        allowed_projects: Optional[List[str]] = self._levels_remote_service.get_allowed_projects(operator_user.token)

        configs: Optional[List[ConfigItem]]
        total: int = 0

        configs, total = self._configs_ddb.find_all(
            name,
            LevelPath.canonize(path) if path is not None else None,
            page_number=page_number,
            page_size=page_size,
            allowed_projects=allowed_projects)

        if configs is None:
            return None, 0

        return list(
            map(lambda c: CompactConfigModel.from_config_item(c),
                configs)), total

    def get_config(self,
                   operator_user: User,
                   id: str,
                   token_dict: Optional[Dict[str, str]]) -> Optional[ConfigModel]:

        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(
            id)

        if config_item is None:
            log.debug(
                f"getting config: unable to find configuration for id '{id}', operator '{operator_user.username}'"
            )
            return None

        if not self._levels_remote_service.is_visible(config_item.path, token=operator_user.token, check_existence=False):
            log.debug(f"getting config: level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        config_model: ConfigModel = ConfigModel.from_config_item_and_json(config_item, {})

        if token_dict is None:
            extended_token_dict = token_dict
        else:
            extended_token_dict = self._extended_dict_with_model_data(token_dict, config_model.level)

        config_json: Optional[Dict[str, Any]] = self._load_json_config(
            id, token_dict=extended_token_dict)

        if config_json is None:
            log.debug(
                f"getting config: unable to find configuration data file for id '{id}', operator '{operator_user.username}'"
            )
            return None

        config_model.configuration = config_json

        return config_model        

    def get_config_status(self, operator_user: User,
                          id: str) -> Optional[ConfigStatusModel]:

        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(
            id)

        if config_item is None:
            log.debug(
                f"getting config status: unable to find configuration for id '{id}', operator '{operator_user.username}'"
            )
            return None

        if not self._levels_remote_service.is_visible(config_item.path, token=operator_user.token, check_existence=False):
            log.debug(f"getting config status: level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        if config_item.active == 0:
            return ConfigStatusModel(current=False)

        # check all active ones to actually determine the current
        current_config_item = self._configs_ddb.find_current_by_level_and_name(
            level_path=config_item.path, config_name=config_item.name)

        if current_config_item is None:
            log.debug(
                f"Unable to determine the configuration status, for id '{id}', operator '{operator_user.username}'"
            )
            return None

        return ConfigStatusModel(current=(current_config_item.id == id))

    def get_effective_config_preview(self, operator_user: User, id: str,                   
                   token_dict: Optional[Dict[str, str]], inherit: Optional[bool]) -> Optional[ConfigModel]:

        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(id)

        return self._get_effective_config_item_preview(operator_user=operator_user, config_item=config_item, token_dict=token_dict, inherit=inherit)
        
    def _get_effective_config_item_preview(self, operator_user: User, config_item: Optional[ConfigItem], 
                   token_dict: Optional[Dict[str, str]], inherit: Optional[bool], exclude_item: bool = False) -> Optional[ConfigModel]:

        if config_item is None:
            log.debug(
                f"getting effective config preview: unable to find config item for id '{id}', operator '{operator_user.username}'"
            )
            return None
  
        level_path: str = config_item.path
        name: str = config_item.name

        if not self._levels_remote_service.is_visible(level_path, token=operator_user.token, check_existence=False):
            log.debug(f"getting effective config preview: level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        inheritable_ancestors: Optional[List[ConfigItem]] = self._configs_ddb.find_inheritable_ancestors_at_path_for_name_in_bottom_up_order(level_path=level_path, config_name=name)

        if inheritable_ancestors is None:
            inheritable_ancestors = []

        current_deepest: Optional[ConfigItem] = inheritable_ancestors[0] if len(inheritable_ancestors) > 0 else None

        is_preview: bool = True

        if current_deepest is None:
            inheritable_ancestors = [config_item] if not exclude_item else []
        else:
            if current_deepest.id != config_item.id: # deepest is not the config item, then add config item

                # if first item is at same path, then remove in favor of the config item being previewed
                if current_deepest.path == config_item.path:
                    inheritable_ancestors = inheritable_ancestors[1:] # remove the first which is the current deepest

                if not exclude_item:
                    inheritable_ancestors.insert(0, config_item) # insert as deepest

            else: # same id (so, also same name and same path)
                is_preview = False

        if is_preview: # preview may be a property of the model in the future
            log.debug(f"Preparing preview for config id '{config_item.id}'")
        else:
            log.debug(f"Preview config for id '{config_item.id}' matches effective config")

        extended_token_dict: Optional[Dict[str,str]]
        
        if token_dict is None:
            extended_token_dict = token_dict
        else:            
            parsed_level_path: Optional[ParsedLevelPath] = ParsedLevelPath.from_level_path(LevelPath.from_path(level_path))
            if parsed_level_path is None:
                log.debug(
                    f"Unable to calculate the effective configuration at {id}, path is unparseable: {level_path}"
                )
                return None    
            else:
                level_path_model: LevelPathModel = LevelPathModel.from_level_path(parsed_level_path.to_level_path())
                extended_token_dict = self._extended_dict_with_model_data(token_dict, level_path_model)

        inherit_val: bool

        if exclude_item:
            inherit_val = True
        else:
            if inherit is None:
                inherit_val = config_item.inherits
            else:
                inherit_val = inherit

        return self._get_effective_config(inheritable_ancestors=inheritable_ancestors, token_dict=extended_token_dict, inherit=inherit_val)

    def get_effective_config(self, operator_user: User, name: str, level_path: str,                   
                   token_dict: Optional[Dict[str, str]], inherit: bool = True) -> Optional[ConfigModel]:

        if not self._levels_remote_service.is_visible(level_path, token=operator_user.token, check_existence=True):
            log.debug(f"getting effective config: level '{level_path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None

        inheritable_ancestors: Optional[List[ConfigItem]] = self._configs_ddb.find_inheritable_ancestors_at_path_for_name_in_bottom_up_order(level_path=level_path, config_name=name)

        if inheritable_ancestors is None:
            log.debug(
                f"Unable to determine the configuration ancestors, for name '{name}', path '{level_path}', operator '{operator_user.username}'"
            )
            return None
        
        extended_token_dict: Optional[Dict[str,str]]
        
        if token_dict is None:
            extended_token_dict = token_dict
        else:
            parsed_level_path: Optional[ParsedLevelPath] = ParsedLevelPath.from_level_path(LevelPath.from_path(level_path))
            if parsed_level_path is None:
                log.debug(
                    f"Unable to calculate the effective configuration, path is unparseable: {level_path}"
                )
                return None    
            else:
                level_path_model: LevelPathModel = LevelPathModel.from_level_path(parsed_level_path.to_level_path())
                extended_token_dict = self._extended_dict_with_model_data(token_dict, level_path_model)

        return self._get_effective_config(inheritable_ancestors=inheritable_ancestors, token_dict=extended_token_dict, inherit=inherit)
        
    def _get_effective_config(self, inheritable_ancestors: List[ConfigItem],                   
                   token_dict: Optional[Dict[str, str]], inherit: bool = True) -> Optional[ConfigModel]:
        
        effective_config: Optional[ConfigModel] = self._calculate_effective_config(inheritable_ancestors, token_dict, inherit)

        if effective_config is None:
            log.debug(
                f"Unable to calculate the effective configuration using: {inheritable_ancestors}"
            )
            return None

        return effective_config

    def delete_config(self, operator_user: User, id: str) -> Optional[bool]:

        config_item: Optional[ConfigItem] = self._configs_ddb.get_config_by_id(
            id)

        if config_item is None:
            log.debug(
                f"deleting config: unable to find configuration for id '{id}', operator '{operator_user.username}'"
            )
            return None
        
        if not self._levels_remote_service.is_visible(config_item.path, token=operator_user.token, check_existence=False):
            log.debug(f"deleting config: level '{config_item.path}' not found or insufficient permissions for operator '{operator_user.username}'")
            return None
        
        if config_item.active > 0:
            raise StatusException(code=409, message="Unable to delete configuration because it is active")

        deleted_item: Optional[ConfigItem] = self._configs_ddb.delete_config_by_id(id)

        if deleted_item is None:
            return False

        if not self._remove_json_config(id):
            log.debug(
                f"Unable to remove configuration data file for id '{id}', operator '{operator_user.username}'"
            )
            return False

        return True

    def _calculate_effective_config(self, bottom_up_inheritables: List[ConfigItem], token_dict: Optional[Dict[str,str]], inherit: bool) -> Optional[ConfigModel]:

        if len(bottom_up_inheritables) == 0:
            return None            
        
        effective_model: Optional[ConfigModel] = None
        base_model: Optional[ConfigModel] = None

        for i_config in bottom_up_inheritables: # first in list is the deepest:

                config_json: Optional[Dict[str, Any]] = self._load_json_config(
                    i_config.id, token_dict=None) # do not replace tokens on each load

                if config_json is None:
                    log.warning(f"Unable to find configuration data file for id '{i_config.id}' during effective config calculation")
                    return None

                config_model: ConfigModel = ConfigModel.from_config_item_and_json(config_item=i_config, config_json=config_json)

                if effective_model is None: # at first iteration the config_model becomes the effective one
                    effective_model = config_model
                    base_model = config_model # keep track of the first model
                    log.debug(f"Using config {i_config.id}, path {i_config.path}, as base for effective config calculation (inherit is {inherit})")

                    if not inherit:
                        break

                    continue                    
            
                # merge config_model into built_model:

                log.debug(f"Merging config {i_config.id}, path {i_config.path}, into previous calculated config model")

                merged_config: Dict[str, Any] = self._merge_configs(effective_model.configuration, config_model.configuration)

                effective_model.configuration = merged_config
        
        if base_model is None or effective_model is None:
            return None # won't happen due to initial validations

        if token_dict is None: # if not token resolving needing, return the effective model
            return effective_model

        try:

            effective_model_configuration_str: str = jsonpickle.encode(effective_model.configuration, unpicklable=True, keys=True)  # type: ignore

            tokenized_config_str = self._fill_tokens(json_data=effective_model_configuration_str, token_dict=token_dict) 

            tokenized_config: Dict[str, Any] = jsonpickle.decode(tokenized_config_str)  # type: ignore

            effective_model.configuration = tokenized_config # replace the effective config with the effective tokenized config        

            return effective_model # return the built/merged model            

        except BaseException as be:
            log.error(f"Unable to tokenize built effective config model: {be}")
            return None
        
    def _extended_dict_with_model_data(self, base_dict: Dict[str,str], level_model: Optional[LevelPathModel]) -> Dict[str,str]:

        extended_dict = copy.deepcopy(base_dict)

        if level_model is None:
            return extended_dict
        
        if level_model is not None:

            if level_model.site is not None:
                extended_dict['site'] = level_model.site

            if level_model.division is not None:
                extended_dict['division'] = level_model.division
                    
            if level_model.show is not None:
                extended_dict['show'] = level_model.show
        
            if level_model.sequence_type is not None:
                extended_dict['sequence_type'] = level_model.sequence_type

            if level_model.sequence is not None:
                extended_dict['sequence'] = level_model.sequence
                    
            if level_model.shot is not None:
                extended_dict['shot'] = level_model.shot

        return extended_dict

    def _inherited_configuration(self, parent_config: Dict[str,Any], child_config: Dict[str,Any], remove_missing: bool) -> Dict[str,Any]:

        # child_config is the deepest, get all keys from parent_config but add keys or override with child values

        result_config: Dict[str, Any] = copy.deepcopy(parent_config) # use parent as base

        if remove_missing: # iterate over parent to not include in result properties missing from child
            for k, v in parent_config.items():
                if not k in child_config:
                    del(result_config[k])

        for k, v in child_config.items(): # iterate over child keys to add them or override parent inherited values

            if not k in result_config: # if key not present in base, and was in child then add it
                result_config[k] = v  # adding new key+value to result
                continue
        
            base_v_at_k = result_config.get(k) # get the value for existing key in base
            if base_v_at_k is not None and type(base_v_at_k) == dict and type(v) == dict: # recursively merge if both are dicts
                merged_dict = self._inherited_configuration(base_v_at_k, v, remove_missing=True) # type: ignore
                result_config[k] = merged_dict
            else:
                result_config[k] = child_config[k]        
            
        return result_config


    def _merge_configs(self, base_config: Dict[str,Any], to_merge: Dict[str,Any]) -> Dict[str,Any]:

        # base_config is the deepest, so no overriding of keys needed when to_merge has the same key, only new keys in to_merge are added

        merged_config: Dict[str, Any] = copy.deepcopy(base_config)

        for k, v in to_merge.items():

            if not k in merged_config: # if key not present in base, then use it
                merged_config[k] = v  # adding new key to base, because it was no present (with or without value)
                continue

            base_v_at_k = merged_config.get(k) # get the value for existing key in base

            if base_v_at_k is not None and type(base_v_at_k) == dict and type(v) == dict: # recursively merge if both are dicts
                merged_dict = self._merge_configs(base_v_at_k, v) # type: ignore
                merged_config[k] = merged_dict
            
        return merged_config

    def _reduced_configuration(self, config: Dict[str,Any], base_config: Dict[str,Any]) -> Dict[str,Any]:

        reduced_config: Dict[str, Any] = {}

        for k, v in config.items():

            if not k in base_config: # if key not present in base, then add
                reduced_config[k] = v
                continue

            base_v_at_k = base_config.get(k) # get the value for existing key k in base

            if base_v_at_k is not None and type(base_v_at_k) == dict and type(config[k]) == dict: # recursively reduce if both are dicts
                reduced_config[k] = self._reduced_configuration(config[k], base_v_at_k) # type: ignore
            else:
                if config[k] != base_v_at_k: # if the config value differs from base value, then include it with the config value
                    reduced_config[k] = config[k]

        return reduced_config

    def _fill_tokens(self,
                     json_data: str,
                     token_dict: Optional[Dict[str, str]]) -> str:

        if token_dict is None:
            return json_data
                
        remaining_data: str = json_data
        ready_json_data: str = ""
                
        while len(remaining_data) > 0:
            match = re.fullmatch(f"(^.*?)({TOKEN_DELIMITER})(.*$)", remaining_data)
            if match is None:
                break
            token_name: str = match.group(4) # token referenced by delimiter is in group (parens) marked inside delimiter str value
            if token_name in token_dict and match.group(3) is not None and match.group(5) is not None: # is is a dict key, use its value
                token_value: Optional[str] = token_dict.get(token_name)                
                ready_json_data = f"{ready_json_data}{match.group(1)}{match.group(3) or ''}{token_value or match.group(4)}{match.group(5) or ''}"
            else:
                ready_json_data = f"{ready_json_data}{match.group(1)}{match.group(2)}"                    
            remaining_data = f"{match.group(6)}"            
                        
        return f"{ready_json_data}{remaining_data}"

    def _load_json_config(
            self, id: str,
            token_dict: Optional[Dict[str, str]]) -> Optional[Dict[str, Any]]:

        source_filename: str = self.__filename_from_id(id)

        log.debug(f"Loading json config data from  {source_filename}")

        try:
            with open(source_filename, "r") as json_file:
                json_data = json_file.read()
                if token_dict is not None:
                    json_data = self._fill_tokens(
                        json_data=json_data,
                        token_dict=token_dict)
                config_json: Optional[Dict[str, Any]] = jsonpickle.decode(json_data)  # type: ignore
            return config_json
        except Exception as e:
            log.error(f"Reading from json config data file failed: {e}")

        return None

    def _write_json_config(self, id: str, config_json: Dict[str, Any]):

        target_filename: str = self.__filename_from_id(id)

        log.debug(f"Saving json config data into {target_filename}")

        try:
            with open(target_filename, "w") as json_file:
                json_data: str = jsonpickle.encode(config_json, unpicklable=True, keys=True)  # type: ignore
                json_file.write(json_data)
        except Exception as e:
            log.error(f"Writing to json config data file failed: {e}")
            return False

        return True

    def _remove_json_config(self, id: str):

        target_filename: str = self.__filename_from_id(id)

        try:
            os.remove(target_filename)
        except Exception as e:
            log.error(f"Deleting json config data file failed: {e}")
            return False

        return True

    def __filename_from_id(self, id: str) -> str:

        return f"{str(Path(self._configs_settings.CONFIGS_DATA_BASEPATH, id))}.json"
