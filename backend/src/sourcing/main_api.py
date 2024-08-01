"""
    Sourcing Service

    This API is for the event sourcing service. It receives data via shotgrid and other external services webhooks and then pushes events into the aws eb, for
    other services like the scheduler service to use.

    This is the entry point for the sourcing service fastapi application.
"""

from typing import Dict

from fastapi import FastAPI

from common.api.info_api import router as info_router
from common.utils import Utils

from sourcing.api.events_api import router as events_router
from sourcing.api.stats_api import router as stats_router

app = FastAPI(
    title="Sourcing Service",
    description="This service receive events from external systems like shotgrid and pushes events into the "
                "internally shared event bus",
    version="1.0.0",
)

app.include_router(info_router)
app.include_router(events_router)
app.include_router(stats_router)

Utils.register_docs(app)

@app.get("/", status_code=200, summary="Ping endpoint")
async def root() -> Dict[str, str]:
    return {"message": "SOURCING service running!"}
