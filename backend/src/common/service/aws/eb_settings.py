from pydantic import BaseSettings

from common.logger import log


class EbSettings(BaseSettings):
    """Holds the configurable env vars used to indicate which aws bus to use and the credentials to use so.

    Also includes vars to mock the event bus when sending events.
    """

    # The following vars contains the credentials used when using the aws eb service:
    EB_REGION_NAME: str = 'us-east-1'
    EB_ACCESS_KEY_ID: str = ''
    EB_SECRET_ACCESS_KEY: str = ''

    EB_VALIDATION_BUS_NAME: str = "dev-bus"
    """Name for the bus used for profile validation events.
    """

    EB_SOURCING_BUS_NAME: str = "dev-sourcing-bus"
    """Name for the bus used internally for handling events related to external changes like the one shotgrid signals via webhooks.
    """

    EB_SCHEDULER_BUS_NAME: str = "dev-scheduler-bus"
    """Name for the bus used internally for handling events related to job scheduling and progress during execution.
    """

    EB_MOCK_EVENTBUS: bool = False
    """Indicates if the event bus most be mocked when events are sent to the aws bus.

    This is used during most tests executions or during local development.
    """

    def __init__(self):
        log.debug("Loading EB settings")
        super(EbSettings, self ).__init__() # type: ignore

    def current_validation_eventbus(self) -> str:
        # TODO: make configurable
        # return f"{self.current_tables_userid()}{self.validation_eventbus}{self.test_session_random}"
        return f"{self.EB_VALIDATION_BUS_NAME}"
    
    def current_sourcing_eventbus(self) -> str:
        # TODO: make configurable
        # return f"{self.current_tables_userid()}{self.sourcing_eventbus}{self.test_session_random}"
        return f"{self.EB_SOURCING_BUS_NAME}"

