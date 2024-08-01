# coding: utf-8

from typing import Dict, Any, Optional

import requests
from fastapi import HTTPException

from common.logger import log
from common.ms_settings import MsSettings
from common.domain.config_name import ConfigName
from common.utils import Utils


class ConfigsRemoteService:
    """Methods to consume the configs microservice.
    """

    _settings: MsSettings

    def __init__(self, settings: MsSettings):

        self._settings = settings
        return

    def get_config(self, name: str, path: str,
                   token: str) -> Optional[Dict[str, Any]]:

    #     if not self._is_config_accesible_for_token(name, path, token):
    #         log.debug(f"[CONFIGS] config path '{path}' is not accesible for token '{Utils.simplify_token(token)}'")

        try:
            return self._get_config(name=name, path=path, token=token)
        except BaseException as be:
            log.error(f"Error while fetching profile. {be}")

        return None

    def _get_config(self, name: str, path: str,
                    token: Optional[str]) -> Optional[Dict[str, Any]]:

        if not path.startswith("/"):
            raise HTTPException(status_code=422,
                                detail="path syntax incorrect")
        
        if not ConfigName.is_name_valid(name):
            raise HTTPException(status_code=422,
                                detail="config name syntax incorrect")

        url = f"{self._settings.MS_CONFIGS_BASE_URL}/configs/current/{name}?path={path}&resolve=true&inherit=true"

        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"} 
                if token is not None else {},
                timeout=(self._settings.MS_CONFIGS_CLIENT_CONN_TIMEOUT,self._settings.MS_CONFIGS_CLIENT_READ_TIMEOUT))
        except BaseException as e:
            log.error(
                f"[CONFIGS] error while attempting to use remote service at '{url} using token '{Utils.simplify_token(token)}': {e}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Temporary error using a remote service")

        if response.status_code == 404 and str(
                response.content).lower().find("no effective configuration available") > 0:
            log.debug(
                f"[CONFIGS] config/path not found according to remote service. config name '{name}', path '{path}', token '{Utils.simplify_token(token)}'"
            )
            return None

        if response.status_code != 200: 
            log.warning(
                f"[CONFIGS] remote service answered with code {response.status_code}: {str(response.content)}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=
                f"remote service answered: {response.status_code}: {str(response.content)}"
            )

        try:
            json = response.json()  # json.dumps(response.json())
        except BaseException as e:
            log.error(
                f"[CONFIGS] remote service answered with invalid json: {str(response.content)}: {e}"
            )
            raise HTTPException(
                status_code=503,
                detail="Temporary error using a remote service")

        r_name: Optional[str] = json.get("name", None)

        if r_name is None or not r_name == name:
            log.warning(
                f"[CONFIGS] remote service answer is unusable, config name is missing or name mismatch: {str(response.content)}"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Temporary error using a remote service")

        return json