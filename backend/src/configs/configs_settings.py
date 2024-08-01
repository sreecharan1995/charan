from functools import lru_cache

from common.auth.auth_settings import AuthSettings
from common.build_settings import BuildSettings
from common.logger import log
from common.ms_settings import MsSettings
from common.service.aws.ddb_settings import DdbSettings
from common.service.aws.eb_settings import EbSettings
from common.service.page_settings import PageSettings


class ConfigsSettings(BuildSettings, AuthSettings, PageSettings, DdbSettings, EbSettings, MsSettings):
    """Represents the set of env vars needed to configure the "configs" api service

    The app will normally receive is settings from environment variables having names that match the var names contained in this class.
    """

    CONFIGS_TABLE: str = "configs"
    """Name of the dynamodb table where info about level-attachable configs is to be stored.

    The actual name will depend on other configuration settings. For example, a prefix is added.
    """

    CONFIGS_DATA_BASEPATH: str = "/tmp"
    """The directory where the json config data files are stored.
    """

    def __init__(self):
        log.debug("Loading CONFIGS settings")
        super(ConfigsSettings, self).__init__()

    def current_configs_table(self) -> str:
        """Returns the actual table name for configs.
        """
        return self._table_name(self.CONFIGS_TABLE)

    class Config:  # type: ignore
        env_file = ".env"  # type: ignore
        env_file_encoding = "utf-8"  # type: ignore

    @staticmethod
    @lru_cache()
    def load_configs() -> 'ConfigsSettings':
        return ConfigsSettings()
