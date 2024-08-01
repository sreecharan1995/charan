
"""
    Levels Health

    This is the entry point for the health assesment code.
"""

from common.logger import log
from common.utils import Utils
from level.level_settings import LevelSettings

if __name__ == '__main__':
            
    log.info("Running in mode 'sync health check'")

    settings: LevelSettings = LevelSettings.load()

    tracking_file: str = settings.LVL_SYNC_HEALTH_TRACKING_FILE
    max_allowed_file_age_in_seconds: int = settings.LVL_SYNC_HEALTH_TRACKING_FILE_MAX_AGE

    return_code: int = Utils.check_max_file_age(tracking_file=tracking_file, max_allowed_file_age_in_seconds=max_allowed_file_age_in_seconds)

    exit(return_code)
