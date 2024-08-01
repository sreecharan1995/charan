## coding: utf-8

from typing import List, Optional

import requests
from fastapi import HTTPException

from common.domain.level_path import LevelPath
from common.logger import log
from common.ms_settings import MsSettings
from common.utils import Utils


class LevelsRemoteService:
    """Methods to consume the levels microservice.
    """

    _settings: MsSettings

    def __init__(self, settings: MsSettings):

        self._settings = settings
        return


    def is_visible(self, path: str, token: Optional[str], check_existence: bool = True) -> bool:

        if not self._is_path_accesible_for_token(path, token):
            log.debug(f"[LEVELS] path '{path}' is not accesible for token '{Utils.simplify_token(token)}'")
            return False
        
        if not check_existence:
            return True

        if self._settings.MS_LEVELS_SKIP_EXISTENCE_CHECK:
            log.warning(f"[LEVELS] Skipping level path '{path}' existence check because of configuration settings")
            return True

        try:
            log.debug(f"[LEVELS] Remote-checking existence of level path '{path}', token '{Utils.simplify_token(token)}'")
            return self._get_level(path, token) is not None
        except BaseException as be:
            log.error(f"[LEVELS] Error while remote-checking path existence: {be}")
            raise be   
        
    def get_allowed_projects(self, token: Optional[str]) -> Optional[List[str]]:

        # TODO: TBI: extract project names from token
        log.warning(f"[LEVELS] TBI: checking projects allowed by token permissions, token '{Utils.simplify_token(token)}'")
        return None # TODO: TBI: warning: None will disable restrictions
        
    def _is_path_accesible_for_token(self, path: str, token: Optional[str]) -> bool:
        # TODO: TBI
        log.warning(f"[LEVELS] TBI: checking token permission for path project '{path}', token '{Utils.simplify_token(token)}'")
        return True
        
    def _get_level(self, path: str, token: Optional[str]) -> Optional[LevelPath]:

        if not path.startswith("/"):
            raise HTTPException(status_code=422, detail="path syntax incorrect")

        url = f"{self._settings.MS_LEVELS_BASE_URL}/levels?path={path}"
          
        try:        
            response = requests.get(url, headers={"Authorization": f"Bearer {token}"} if token is not None else {}, timeout=(self._settings.MS_LEVELS_CLIENT_CONN_TIMEOUT, self._settings.MS_LEVELS_CLIENT_READ_TIMEOUT))
        except BaseException as e:
            log.error(f"[LEVELS] error while attempting to use remote service at '{url} using token '{Utils.simplify_token(token)}': {e}")
            raise HTTPException(status_code=503, detail=f"Temporary error using a remote service")

        if response.status_code == 404 and str(response.content).lower().find("level not found"):
            log.debug(f"[LEVELS] path not found according to remote service. path '{path}', token '{Utils.simplify_token(token)}'")
            return None

        if response.status_code != 200:                    
            log.warning(f"[LEVELS] remote service answered with code {response.status_code}: {str(response.content)}")
            raise HTTPException(status_code=response.status_code, detail=f"remote service answered: {response.status_code}: {str(response.content)}")   

        try:
            json = response.json() # json.dumps(response.json())
        except BaseException as e:
            log.error(f"[LEVELS] remote service answered with invalid json: {str(response.content)}: {e}")
            raise HTTPException(status_code=503, detail="Temporary error using a remote service")

        r_path: Optional[str] = json.get("path", None)

        if r_path is None:
            log.warning(f"[LEVELS] remote service answer is unusable, path is missing: {str(response.content)}")
            raise HTTPException(status_code=503, detail=f"Temporary error using a remote service")

        return LevelPath(r_path)
        