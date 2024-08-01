from functools import lru_cache

from common.auth.auth_settings import AuthSettings
from common.build_settings import BuildSettings
from common.logger import log
from common.service.aws.eb_settings import EbSettings
from common.service.sg.sg_settings import SgSettings
from common.service.aws.ddb_settings import DdbSettings
from common.ms_settings import MsSettings


class SchedulerSettings(BuildSettings, AuthSettings, EbSettings, SgSettings, MsSettings, DdbSettings):
    """Represents the set of env vars needed to configure the "scheduler" api service

    The app will normally receive its settings from environment variables having names that match the var names contained in this class.
    """

    ESCH_EVENT_TOOLS_CONFIG_NAME: str = "event_tools"    
    """Config name containing the tool settings per sg event type, to be looked up in configs microservice
    """

    ESCH_JOBREQUEST_TABLE: str = "jobrequest"
    """Name of the dynamodb table where data about job requests is stored.

    The actual name will depend on other configuration settings. For example, a prefix is added.

    This table is used to create/register jobs that need to be executed, and also read jobs that need to be executed.
    """

    ESCH_SCHEDULER_DDB_TABLE_JOBREQUEST_CATALOG: str = "global"
    """A fixed partition key (catalog) used for dynamodb table partitioning.
    
    This is normally unchanged. It's used in combination with a range key (time based) when creating or requesting requests in table.
    """

    ESCH_JOBREQUEST_RECHECK_WAIT: int = 60  # scheduler exec process waits this number of seconds before checking if there are new job requests    
    """The number of seconds to wait before checking again for new job request
    """

    ESCH_JOB_PODS_TTL_HOURS: int = 72  
    """The number of hours kubernetes jobs and related pods will be around after completion or failure
    """

    ESCH_JOB_BACKOFF_LIMIT: int = 2
    """The max number of attempt to execute a job container pod when it returns a non zero exit code
    """

    ESCH_EXEC_HEALTH_TRACKING_FILE: str = "/tmp/last-successful-scheduler-exec-iteration"
    """Name of file created and updated by the scheduler exec process on each iteration to prove its main iteration cycle is alive.

    Kubernetes readiness and health checks use this file last-changed date indirectly to asses the app container health.
    """

    ESCH_EXEC_HEALTH_TRACKING_FILE_MAX_AGE: int = 60 * 2 # default in seconds: 2 times the recheck iteration wait (means: 2 iterations)    
    """Max age of the health tracking file to consider healthy the main iteration cycle.

    The entry point checking for the scheduler exec process main cycle health uses this value to determine if will give a positive or negative response when 
    requested for health assesment.
    """

    ESCH_EXEC_TOOL_K8_MAX_JOBREQUESTS: int = 10
    """Max number of jobs requests to run as k8 Jobs in the same exec iteration
    """

    ESCH_TAPI_IMAGE_TAG: str = "spinvfx/tapi"
    """Tag of the tapi docker pre-built image to use in k8 jobs when running tools
    """

    # ESCH_EXEC_TOOL_MARKS_VALIDATION: bool = True
    # """If the exec tool entry point should validate job request marks before proceeding. Useful during development/debugging.        
    # """
    
    ESCH_SG_DEFAULT_SITE: str = "Toronto"
    """Default site when looking up configs for sg events not expliciting mentioning a site, or no calculation possible
    """

    ESCH_JOBCONF_BASEDIR: str = "/mount/sg-event-scripts/job_conf"
    """Base directory where the job scheduler stores the configuration (tool config, original event and profile config)
       so the job pod entrypoint can later read it when the tool is executed inside the pod, the rez-env is setup, etc.
    """

    def __init__(self):
        log.debug("Loading ESCH settings")
        super(SchedulerSettings, self).__init__()

    class Config:  # type: ignore
        env_file = ".env"  # type: ignore
        env_file_encoding = "utf-8"  # type: ignore

    def current_jobrequest_table(self) -> str:        
        """Returns the actual jobrequest table name.
        """
        return self._table_name(self.ESCH_JOBREQUEST_TABLE)

    @staticmethod
    @lru_cache()
    def load() -> 'SchedulerSettings':
        return SchedulerSettings()
