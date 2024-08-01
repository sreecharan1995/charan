import logging

from shotgun_api3 import Shotgun # type: ignore
from fastapi import APIRouter

from dependency.dependency_settings import DependencySettings

router = APIRouter()
settings = DependencySettings.load()
log = logging.getLogger("uvicorn")

try:
    sg = Shotgun(
        settings.SG_URL,
        script_name=settings.SG_SCRIPT_NAME,
        api_key=settings.SG_API_KEY,
        connect=False,
    )
except BaseException as be:
    log.error(type(be))
    sg = None


@router.get("/test")
def test_api(): # type: ignore
    # result = sg.schema_read()
    # result = sg.find("HumanUser", [], ["firstname", "lastname", "profile_role"])
    # result = sg.find("Group", [], ["code", "notes", "open_notes", "tags"])
    result = sg.find("PermissionRuleSet", [], ["display_name", "parent_set", "properties"]) # type: ignore
    return result # type: ignore
