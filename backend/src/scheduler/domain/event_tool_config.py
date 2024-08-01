
from typing import Any, Dict, Optional
from common.logger import log

class EventToolConfig():
    """Represents the configuration which is mapped from an event type in the looked up remote config microservice for the event-calculated level.
    """

    tool_to_run: str
    """the path of the tool to run in the rez-env 
    """

    profile_id: Optional[str] # profile id takes precedence over profile path
    """a profile id to use to extract its path level when calculating the dependencies against the remote dependencies microservice

    If set then no event-calculated level occurs and profile_path is also ignored.
    """

    profile_path: Optional[str] # profile path is autodetected but can be forced (however profile_id takes precedence when getting profile path)
    """a path to use when calculating the dependencies against the remote dependencies microservice

    If set then no event-calculated level occurs, however profile_id has priority over this setting.
    """

    tool_config: Dict[str,Any]
    """the specific config dict to pass to the tools when run"""

    def __init__(self) -> None:
        pass

    @staticmethod
    def from_dict(json_dict: Dict[str,Any]) -> Optional['EventToolConfig']:
        """Method to create an instance from a config dict.

        This is usually fetched 
        """

        config: EventToolConfig = EventToolConfig()

        try:

            config.tool_to_run = json_dict.get("tool_to_run", "")
            config.profile_id = json_dict.get("profile_id", "")
            config.profile_path = json_dict.get("profile_path", "")
            config.tool_config = json_dict.get("tool_config", dict())
        
        except BaseException as be:
            log.debug(f"Unable to parse config tool configuration {be}")
            return None

        return config