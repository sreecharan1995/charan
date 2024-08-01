from pydantic import BaseSettings
from common.logger import log

class SgSettings(BaseSettings):
    """Represents the set of env vars to configure access to shotgrid    
    """
    
    SG_URL: str = ""
    """the shotgrid api base url
    """

    SG_SCRIPT_NAME: str = ""
    """the shotgrid script name used when connecting to api
    """

    SG_API_KEY: str = ""
    """the api key used to authenticate as a client to shotgrid
    """

    SG_PROXY: str = ""
    """the proxy to use when connecting to sg, if set
    """

    def __init__(self):
        log.debug("Loading SG settings")
        super(SgSettings, self).__init__() # type: ignore