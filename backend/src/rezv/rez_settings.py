import uuid
from functools import lru_cache
from pathlib import Path
from typing import Optional

from common.build_settings import BuildSettings
from common.logger import log
from common.service.aws.eb_settings import EbSettings


class RezSettings(BuildSettings, EbSettings):
    """Represents the set of env vars needed to configure the "rezv" api service

    The app will normally receive is settings from environment variables having names that match the var names contained in this class.
    """

    MOCK_EVENTBUS: bool = False
    """Whether the events triggered by this service will actually reach the event bus or not.

    If true events will be mocked and stored in a local internal list.
    """

    ### REZ configuration.
    # https://github.com/AcademySoftwareFoundation/rez/wiki/Configuring-Rez#configuration-settings
    packages_path: str = ""

    # base path where to store produced rxt files
    rxt_path: str = "/tmp"

    def __init__(self):
        log.debug("Loading REZV settings")
        super(RezSettings, self).__init__()

    def new_rxt_path(self, profile_id: str) -> Optional[str]:
        if self.packages_path is None:
            return None
        base_path : str = self.rxt_path.strip()
        unique : str = str(uuid.uuid4())[0:8]
        file_name : str = f"profile-{profile_id}.{unique}.rxt"
        return str(Path(base_path, file_name))


    @staticmethod
    @lru_cache()    
    def load() -> 'RezSettings':
        return RezSettings()
        
    class Config: # type: ignore
        env_file = ".env"
        env_file_encoding = "utf-8"



