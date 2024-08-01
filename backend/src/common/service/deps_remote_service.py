## coding: utf-8

from typing import Optional, List

import requests
from fastapi import HTTPException

from common.logger import log
from common.ms_settings import MsSettings
from common.utils import Utils


class DepsRemoteService:
    """Methods to consume the dependencies microservice.
    """

    _settings: MsSettings

    def __init__(self, settings: MsSettings):

        self._settings = settings
        return

    def get_profile_packages(self, profile_id: str, token: str) -> Optional[List[str]]:
        
        try:
            return self._get_profile_packages_list(profile_id=profile_id, token=token)
        except BaseException as be:
            log.error(f"Error while fetching profile path packages. {be}")

        return None
    
    def get_path_packages(self, profile_path: str, token: str) -> Optional[List[str]]:
        
        try:
            return self._get_path_packages_list(profile_path=profile_path, token=token)
        except BaseException as be:
            log.error(f"Error while fetching path packages. {be}")

        return None
        
    def _get_profile_packages_list(self, profile_id: str, token: Optional[str]) -> Optional[List[str]]:
        
        url = f"{self._settings.MS_DEPS_BASE_URL}/profiles/{profile_id}/all"
          
        try:        
            response = requests.get(url, headers={"Authorization": f"Bearer {token}"} if token is not None else {}, timeout=(self._settings.MS_DEPS_CLIENT_CONN_TIMEOUT, self._settings.MS_DEPS_CLIENT_READ_TIMEOUT))
        except BaseException as e:
            log.error(f"[DEPS] error while attempting to use remote service at '{url} using token '{Utils.simplify_token(token)}': {e}")
            raise HTTPException(status_code=503, detail=f"Temporary error using a remote service")

        if response.status_code == 404 and str(response.content).lower().find("profile not found"):
            log.debug(f"[DEPS] profile not found according to remote service. profile_id '{profile_id}', token '{Utils.simplify_token(token)}'")
            return None

        if response.status_code != 200:                    
            log.warning(f"[DEPS] remote service answered with code {response.status_code}: {str(response.content)}")
            raise HTTPException(status_code=response.status_code, detail=f"remote service answered: {response.status_code}: {str(response.content)}")   

        try:
            json = response.json() # json.dumps(response.json())
        except BaseException as e:
            log.error(f"[DEPS] remote service answered with invalid json: {str(response.content)}: {e}")
            raise HTTPException(status_code=503, detail="Temporary error using a remote service")

        return json
        
        
    def _get_path_packages_list(self, profile_path: str, token: Optional[str]) -> Optional[List[str]]:

        url = f"{self._settings.MS_DEPS_BASE_URL}/effective-profile/all?path={profile_path}"
          
        try:        
            response = requests.get(url, headers={"Authorization": f"Bearer {token}"} if token is not None else {}, timeout=(self._settings.MS_DEPS_CLIENT_CONN_TIMEOUT, self._settings.MS_DEPS_CLIENT_READ_TIMEOUT))
        except BaseException as e:
            log.error(f"[DEPS] error while attempting to use remote service at '{url} using token '{Utils.simplify_token(token)}': {e}")
            raise HTTPException(status_code=503, detail=f"Temporary error using a remote service")

        # if response.status_code == 404 and str(response.content).lower().find("profile not found"):
        #     log.debug(f"[DEPS] profile not found according to remote service. profile_id '{profile_id}', token '{Utils.simplify_token(token)}'")
        #     return None

        if response.status_code != 200:                    
            log.warning(f"[DEPS] remote service answered with code {response.status_code}: {str(response.content)}")
            raise HTTPException(status_code=response.status_code, detail=f"remote service answered: {response.status_code}: {str(response.content)}")   

        try:
            json = response.json() # json.dumps(response.json())
        except BaseException as e:
            log.error(f"[DEPS] remote service answered with invalid json: {str(response.content)}: {e}")
            raise HTTPException(status_code=503, detail="Temporary error using a remote service")

        return json
                