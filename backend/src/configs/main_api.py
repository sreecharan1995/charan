# coding: utf-8

"""
    Software Configuration Service

    This API allows for the management of configurations for different DCC tools.
    It also allows for the linking of configurations to a particular 'level'. (See Level's service).

    This is the entry point for the configs service fastapi application.

"""

from fastapi import FastAPI

from common.api.auth_info_api import router as AuthInfoApiRouter
from common.api.info_api import router as InfoApiRouter
from common.logger import log
from common.utils import Utils
from configs.api.configs_api import router as ConfigsApiRouter
from configs.configs_settings import ConfigsSettings
from configs.service.aws.configs_ddb import ConfigsDdb
from dependency.api.index_api import router as IndexApiRouter

app = FastAPI(
    title="Software Configuration Service",
    description="This API allows for the management of configuration for different DCC tools. "
                "It also allows for the linking of configurations to a particular 'level'.  (See Level's service).",
    version="1.0.0",
)

app.include_router(IndexApiRouter)
app.include_router(InfoApiRouter)
app.include_router(AuthInfoApiRouter)
app.include_router(ConfigsApiRouter)

Utils.register_docs(app)

settings = ConfigsSettings.load_configs()

configs_ddb = ConfigsDdb(settings=settings)

if not configs_ddb.create_tables():
    log.warning("Initialization failed")
    exit(1)
