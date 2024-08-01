from functools import lru_cache

from common.auth.auth_settings import AuthSettings
from common.build_settings import BuildSettings
from common.logger import log
from common.ms_settings import MsSettings
from common.service.aws.ddb_settings import DdbSettings
from common.service.aws.eb_settings import EbSettings
from common.service.page_settings import PageSettings
from common.service.sg.sg_settings import SgSettings


class DependencySettings(BuildSettings, AuthSettings, PageSettings, DdbSettings, EbSettings, SgSettings, MsSettings):
    """Represents the set of env vars needed to configure the "dependency" api service

    The app will normally receive is settings from environment variables having names that match the var names contained in this class.
    """

    DEP_PACKAGES_DIRECTORY_PATH: str = ""
    """Directory path where the available packages files are detected and read from.
    """

    DEP_PROFILES_TABLE: str = "profiles"
    """Name of the dynamodb table where data about profiles is to be stored.

    The actual name will depend on other configuration settings. For example, a prefix is added.
    """

    DEP_BUNDLES_TABLE: str = "bundles"
    """Name of the dynamodb table where data about bundles is to be stored.

    The actual name will depend on other configuration settings. For example, a prefix is added.
    """

    DEP_SKIP_DESCENDANT_UPDATES: bool = False
    """Whether validation events most be triggered for descendants of a modified profiles, so they are updated, or not
    """

    def __init__(self):
        log.debug("Loading DEP settings")
        super(DependencySettings, self).__init__()

    def current_profiles_table(self) -> str:
        """Returns the actual table name for profiles.
        """
        return self._table_name(self.DEP_PROFILES_TABLE)

    def current_bundles_table(self) -> str:
        """Returns the actual table name for bundles.
        """
        return self._table_name(self.DEP_BUNDLES_TABLE)

    class Config:  # type: ignore
        env_file = ".env"  # type: ignore
        env_file_encoding = "utf-8"  # type: ignore

    @staticmethod
    @lru_cache()
    def load() -> 'DependencySettings':
        return DependencySettings()
