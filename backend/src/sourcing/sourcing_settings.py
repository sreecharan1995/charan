from functools import lru_cache

from common.auth.auth_settings import AuthSettings
from common.build_settings import BuildSettings
from common.logger import log
from common.service.aws.eb_settings import EbSettings


class SourcingSettings(BuildSettings, AuthSettings, EbSettings):
    """Represents the set of env vars needed to configure the "sourcing" api service

    The app will normally receive its settings from environment variables having names that match the var names contained in this class.
    """    
    
    ESRC_SG_EVENT_SIGNATURE_TOKEN: str = ""
    """Token used by shotgrid when signing the event payload when calling the webhook
    """

    ESRC_REJECT_SG_EVENTS_WITHOUT_CORRECT_SIGNATURES: bool = False
    """Whether events received from shotgrid having no signatures should be rejected or not
    """

    def __init__(self):
        log.debug("Loading ESRC settings")
        super(SourcingSettings, self).__init__()

    class Config:  # type: ignore
        env_file = ".env"  # type: ignore
        env_file_encoding = "utf-8"  # type: ignore

    @staticmethod
    @lru_cache()
    def load() -> 'SourcingSettings':
        return SourcingSettings()
