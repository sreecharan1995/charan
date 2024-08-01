from pydantic import BaseSettings

from common.logger import log


class BuildSettings(BaseSettings):
    """Represents the set of env vars that hold build-time information

    The env vars in this class hold usually hold the values provided by bitbucket when the build pipeline is executed
    to produce a specific build
    """

    BUILD_ID: str = ""
    """The build number assigned during the bitbucket pipeline execution.
    """

    BUILD_DATE: str = ""
    """A formatted date as provided by the bitbucket pipeline, indicating the time when the build was created
    """

    BUILD_HASH: str = ""
    """The git identifier of the changeset used to produce the build, as provided by bitbucket pipeline during execution
    """

    BUILD_IMAGE: str = ""
    """The build image of the current code
    """

    BUILD_LINK: str = ""
    """A string with a url pointing to the bitbucket build page with details regarding the build
    """

    def __init__(self):
        log.debug("Loading BUILD settings")
        super(BuildSettings, self).__init__()  # type: ignore
