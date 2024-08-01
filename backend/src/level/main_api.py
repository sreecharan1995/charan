## coding: utf-8

"""
    Levels Service

    This API is for listing/filtering spinvfx levels.

    This is the entry point for the levels service fastapi application.
"""

# from typing import Optional
from fastapi.applications import FastAPI

from common.api.info_api import router as InfoApiRouter
# from common.domain.sg.shotgrid_publishedfile import ShotgridPublishedFile
# from common.domain.sg.shotgrid_task import ShotgridTask
from common.logger import log
from common.utils import Utils
from level.api.index_api import router as IndexApiRouter
from level.api.levels_api import router as LevelsApiRouter
from level.api.sites_api import router as SiteApiRouter
from level.api.sync_api import router as SyncApiRouter
from level.api.tree_api import router as TreeApiRouter
from level.level_settings import LevelSettings
from level.service.aws.levels_ddb import LevelsDdb

log.info("Running in mode 'levels api server'")

app = FastAPI(
    title="Levels Service",
    description="This API is for listing/filtering spinvfx levels",
    version="1.0.0",
)

app.include_router(InfoApiRouter)
app.include_router(LevelsApiRouter)
app.include_router(SiteApiRouter)
app.include_router(SyncApiRouter)
app.include_router(TreeApiRouter)
app.include_router(IndexApiRouter)

Utils.register_docs(app)

settings = LevelSettings.load()

levels_ddb = LevelsDdb(settings=settings)

if not levels_ddb.create_tables():
    log.warning("Initialization failed")
    exit(1)

######################

# TODO: remove the following lines, used to help debug/test publishedfile misc methods
# from common.service.sg.shotgrid_service import ShotgridService
# sg_service = ShotgridService(settings=settings)
# sg_service.list_fields("Task")
# project_id: int = 235
# sg_pf: Optional[ShotgridPublishedFile] = sg_service.find_project_publishedfile(235, 254920)
# if sg_pf is not None:
#     sg_t: Optional[ShotgridTask] = sg_pf.get_task()
#     if sg_t is not None:
#         t_id: Optional[int] = sg_t.get_id()
#         if t_id is not None:
#             t = sg_service.find_project_task(235, t_id)

