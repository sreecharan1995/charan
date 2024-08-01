from pydantic import BaseSettings

from common.logger import log


class MsSettings(BaseSettings):
    """Represents the set of env vars that configure the client code for external spinvfx microservices.

    The app will normally receive is settings from environment variables having names that match the var names contained in this class.
    """
    
    MS_LEVELS_BASE_URL: str = "https://levels.dev.spinvfx.com"
    """the base URL for the "levels" microservice
    """

    MS_LEVELS_APIKEY: str = ""
    """the key used to authenticate with the levels remote service as an internal client
    """

    MS_LEVELS_CLIENT_CONN_TIMEOUT: int = 5
    """the number of seconds to wait for the remote levels service before timing out connecting
    """
    
    MS_LEVELS_CLIENT_READ_TIMEOUT: int = 5
    """the number of seconds to wait for the remote levels service before timing out reading
    """

    MS_LEVELS_SKIP_EXISTENCE_CHECK: bool = False
    """whether the "levels" microservice client should actually use the remote service or not when checking for level path existence
    """

    MS_CONFIGS_BASE_URL: str = "https://configs.dev.spinvfx.com"
    """the base URL for the "configs" microservice
    """

    MS_CONFIGS_APIKEY: str = ""
    """the key used to authenticate with the configs remote service as an internal client
    """

    MS_CONFIGS_CLIENT_CONN_TIMEOUT: int = 5
    """the number of seconds to wait for the remote configs service before timing out connecting
    """

    MS_CONFIGS_CLIENT_READ_TIMEOUT: int = 5
    """the number of seconds to wait for the remote configs service before timing out reading
    """

    MS_DEPS_BASE_URL: str = "https://dependency.dev.spinvfx.com"
    """the base URL for the "dependency" microservice
    """

    MS_DEPS_APIKEY: str = ""
    """the key used to authenticate with the deps remote service as an internal client
    """

    MS_DEPS_CLIENT_CONN_TIMEOUT: int = 5
    """the number of seconds to wait for the remote deps service before timing out connecting
    """

    MS_DEPS_CLIENT_READ_TIMEOUT: int = 5
    """the number of seconds to wait for the remote deps service before timing out reading
    """
    
    def __init__(self):
        log.debug("Loading MS settings")
        super(MsSettings, self).__init__()  # type: ignore
