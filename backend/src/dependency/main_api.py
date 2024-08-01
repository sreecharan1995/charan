## coding: utf-8

"""
    Software Dependency Service

    This API allows for the management of packages, bundles and profiles. It also allows for the linking of profiles to a particular 'level' in a shotgrid project. 

    This is the entry point for the dependency service fastapi application.
"""

from fastapi import FastAPI

from common.api.auth_info_api import router as AuthInfoApiRouter
from common.api.info_api import router as InfoApiRouter
from common.api.permissions_api import router as PermissionMatrixApiRouter
from common.logger import log
from common.utils import Utils
from dependency.api.bundles_api import router as BundlesApiRouter
from dependency.api.index_api import router as IndexApiRouter
from dependency.api.packages_api import router as PackagesApiRouter
from dependency.api.profiles_api import router as ProfilesApiRouter
from dependency.dependency_settings import DependencySettings
from dependency.service.aws.dependency_ddb import DependencyDdb

app = FastAPI(
    title="Software Dependency Service",
    description="This API allows for the management of packages, bundles and profiles. It also allows for the linking "
                "of profiles to a particular &#39;level&#39; in a shotgrid project. ",
    version="1.0.0",
)

app.include_router(IndexApiRouter)
app.include_router(BundlesApiRouter)
app.include_router(PackagesApiRouter)
app.include_router(ProfilesApiRouter)
app.include_router(InfoApiRouter)
app.include_router(AuthInfoApiRouter)
app.include_router(PermissionMatrixApiRouter)

Utils.register_docs(app)

settings = DependencySettings.load()

dependency_ddb: DependencyDdb = DependencyDdb(settings)

if not dependency_ddb.create_tables():
    log.warning("Initialization failed")
    exit(1)