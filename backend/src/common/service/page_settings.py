from pydantic import BaseSettings

from common.logger import log


class PageSettings(BaseSettings):
    """Holds configurable env vars related to default page sizes.
    """

    DEFAULT_PAGE_SIZE: int = 10

    def __init__(self):
        log.debug("Loading PAGE settings")
        super(PageSettings, self).__init__()  # type: ignore
