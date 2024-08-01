"""
    RezV Service

    This API is for validating profiles data.

    This is the entry point for the rezv service fastapi application.
"""

from fastapi import FastAPI
from rez.config import create_config  # type: ignore
from rez.package_bind import get_bind_modules  # type: ignore

from common.api.info_api import router as info_router
from common.logger import log
from common.utils import Utils
from rezv.api.events_api import router as events_route
from rezv.api.index_api import router as index_router

app = FastAPI(
    title="REZ Service",
    description="This service listen for events about bundles and profiles updates and verifies they can be"
                "resolved by REZ",
    version="1.0.0",
)

app.include_router(events_route)
app.include_router(info_router)
app.include_router(index_router)

Utils.register_docs(app)


@app.get("/", status_code=200, summary="Ping endpoint")
async def root():
    return {"message": "REZ service running!"}


@app.on_event("startup")  # type: ignore
async def startup_event():
    log.info("Starting up")
    config = create_config().data  # type: ignore
    log.debug("REZ configuration: %s", config) # type: ignore
    log.info(f"Bound packages: {get_bind_modules()}")
