from functools import lru_cache
from typing import List

from common.auth.auth_settings import AuthSettings
from common.build_settings import BuildSettings
from common.logger import log
from common.service.aws.ddb_settings import DdbSettings
from common.service.sg.sg_settings import SgSettings


class LevelSettings(BuildSettings, AuthSettings, DdbSettings, SgSettings):
    """Represents the set of env vars needed to configure the "levels" api service

    The app will normally receive is settings from environment variables having names that match the var names contained in this class.

    The configuration on this class is used both by a levels sync process app and a levels api app.

    Sync requests are created as items via endpoint in levels api app, in a dynamodb table that is read with regularity by
    the levels sync process. 

    When new sync requests are detected, a single traversing of the shotgrid projects tree is performed to fulfill all these requests
    at once, and a local serialized representation of remote projects data is persisted on a path shared with the levels api app.
    
    Also the current (previously persisted) local data is loaded and verified to guarantee is usable by the sync process. If any issue
    arises a new sync request is auto-created to deal with in the next iteration of the sync process.
    """

    LVL_SYNC_FILTER_PROJECT_TAGS_TO_AVOID: List[str] = [ "marketing", "internal" ]
    """A list of tags to be avoided when traversing projects data in shotgrid.

    A project is considered when does not have any of the tags included in this list.
    """

    LVL_SYNC_RECHECK_WAIT: int = 60  # sg sync process waits this number of seconds before checking if there are new sync requests    
    """The number of seconds to wait before checking again for new sync request, or to verify the current shared data is usable.
    """

    LVL_SYNC_RESTRICT_TO_PROJECTS: str = "" # command-separated list of project ids. used in local envs to restrict the projects universe only and speedup local development
    """Comma-separated list of shotgrid project ids to use exclusively (ignoring others).

    This parameter makes sense only when used in local development environments where there is no need to fetch data from 
    all potentially available projects, as occurs in production or shared uat environments.
    """

    LVL_SYNC_HEALTH_TRACKING_FILE: str = "/tmp/last-successful-tree-verification"
    """Name of file created and updated by the levels sync process on each iteration to prove its main iteration cycle is alive.

    Kubernetes readiness and health checks use this file last-changed date indirectly to asses the app container health.
    """

    LVL_SYNC_HEALTH_TRACKING_FILE_MAX_AGE: int = 60 * 5 # default in seconds: 5 times the recheck iteration wait (means: 5 iterations)    
    """Max age of the health tracking file to consider healthy the main iteration cycle.

    The entry point checking for the sync process main cycle health uses this value to determine if will give a positive or negative response when 
    requested for health assesment.
    """

    LVL_SYNC_DDB_TABLE_SGTREE_CATALOG: str = "global"
    """A fixed partition key (catalog) used for dynamodb table partitioning.
    
    This is normally unchanged. It's used in combination with a range key (time based) when creating or requesting sync request in table.
    """

    LVL_API_TREE_CACHE_MIN_SECONDS: int = 60 * 2 # 2 min
    """Number of seconds that a loaded shotgrid tree representation is used before considering to use a younger version. 

    The persisted representation of the shotgrid data is loaded and served from the levels api. When the levels sync process fetches data
    from shotgrid an create new shared file representations of it, this data is not inmediatelly used by the levels api, but a minimum amount 
    of time, configured with this var, is needed before discarding the previous data and loading the most recent one.
    """

    LVL_TREE_BASEPATH: str = "/tmp" # folder where the serialized tree is going to be read/written from/to
    """Directory path where the shotgrid projects data representation is persisted.
    
    This directory is shared by the levels sync process and the levels api app, because the first created the files with the 
    projects data representation and the later eventually loads the data to be served.
    """

    LVL_SGTREE_TABLE: str = "sgtree"
    """Name of the dynamodb table where data about sync requests is stored.

    The actual name will depend on other configuration settings. For example, a prefix is added.

    This table is read to both determine the latest available shotgrid projects data tree representation and to determine and fulfill
    new sync requests.
    """

    LVL_ENFORCE_PROJECT_ACCESS_SECURITY: bool = False # TBI: change to True by default for improved security as soon as the data is actually included in the token
    """Whether the access to levels/paths under a project has to be verified against the user token or not before returning data or assessing existance.

    Not every user has access to all projects, so confirming the existence of a project related path or returning any data regarding projects can be delivered only when
    the user has being granted access to the project in question. The information regarding which projects a user has access to is encoded in the user authorization token.
    """
        
    def __init__(self):
        log.debug("Loading LVL settings")
        super(LevelSettings, self).__init__()

    def current_sgtree_table(self) -> str:        
        """Returns the actual sgtree table name.
        """
        return self._table_name(self.LVL_SGTREE_TABLE)

    class Config: # type: ignore
        env_file = ".env"  # type: ignore
        env_file_encoding = "utf-8"  # type: ignore
        
    @staticmethod
    @lru_cache()
    def load() -> 'LevelSettings':
        return LevelSettings()