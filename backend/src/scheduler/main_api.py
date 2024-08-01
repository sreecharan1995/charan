"""
    Scheduler Service

    This API is for the event scheduler service. It receives events from the internal aws event bus and process the ones related to script execution.

    This is the entry point for the scheduler service fastapi application.
"""

from fastapi import FastAPI

from common.api.info_api import router as info_router
from common.utils import Utils

from scheduler.api.events_api import router as scheduler_router

from scheduler.api.dev_api import router as dev_router

app = FastAPI(
    title="Scheduler Service",
    description="This service receive events from the internaly shared event bus to execute the intended tool as "
                "specified in the event",
    version="1.0.0",
)

app.include_router(info_router)
app.include_router(scheduler_router)
app.include_router(dev_router)

Utils.register_docs(app)


@app.get("/", status_code=200, summary="Ping endpoint")
async def root():
    return {"message": "SCHEDULER service running!"}
