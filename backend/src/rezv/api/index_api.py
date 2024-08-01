from fastapi import APIRouter, Request  # noqa: F401

router = APIRouter()


@router.get("/")
async def index(req: Request):
    return "REZ service running ..."
    ## return response
