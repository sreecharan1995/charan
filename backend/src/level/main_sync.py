# coding: utf-8

import time
from typing import List, Optional

from common.logger import log
from common.utils import Utils
from level.domain.sync_request import SyncRequest
from level.level_settings import LevelSettings
from level.service.aws.levels_ddb import LevelsDdb
from level.service.sync_service import SyncService

"""
    Levels sync process

    This process is the one that traverses shotgrid projects and creates a local representation that is in turn persisted to a shared 
    path, or gets verified after each iteration of the main process cycle.

    This is the entry point for the dependency service fastapi application.
"""

if __name__ == '__main__':
    
    log.info("Running in mode 'levels sync'")

    settings: LevelSettings = LevelSettings.load()

    levels_ddb = LevelsDdb(settings=settings)

    if not levels_ddb.create_tables():
        log.warning("Initialization failed")
        exit(1)


    sync_service: SyncService = SyncService(settings)

    seconds_between_checks: int = settings.LVL_SYNC_RECHECK_WAIT

    log.info(
        f"Configured to wait {seconds_between_checks} seconds before checking again for new sync requests"
    )

    while True:

        requests: List[SyncRequest] = sync_service.get_sync_requests()
        requests_count: int = len(requests)

        success: bool = False
        create_new: bool = False

        if requests_count == 0:
            log.debug("No request to create a new tree was found")

            latest: Optional[SyncRequest] = sync_service.get_last_fulfilled_sync_request()

            if latest is None:
                log.warning(
                    "No usable tree snapshot is available, creating a new request for next iteration"
                )
                sync_service.new_sync_request(
                    "self-requested because no previous snapshot was found"
                )
            else:
                if latest.filename is not None:

                    log.debug(
                        f"Found sync request {latest.id}, filename '{latest.filename}', comment: '{latest.comment}'"
                    )

                    log.debug(f"Latest tree snapshot is '{latest.filename}'")

                    verified: bool = sync_service.verify_tree(latest.filename)

                    if not verified:
                        log.info(f"Latest tree unusable. Creating new request for next iteration")
                        sync_service.new_sync_request("self-requested because latest tree verification failed")
                    else:                    
                        health_tracking_file: str = settings.LVL_SYNC_HEALTH_TRACKING_FILE
                        if Utils.touch_file(health_tracking_file):
                            log.debug(f"Updated timestamp of health tracking file {health_tracking_file}")
                        else:
                            log.warning(f"Failed to update timestamp of health tracking file {health_tracking_file}")
                    
        else:

            log.info(f"Found {requests_count} request(s) to create a new tree")

            filename: Optional[str] = None

            filename = sync_service.new_tree()

            if filename is None:
                log.warning("Failed to create a new shotgrid tree snapshot")
            else:
                log.info(f"New shotgrid tree snapshot created: {filename}")

                fulfillments_count: int = sync_service.fulfill_requests(filename, requests)
                if fulfillments_count == requests_count:
                    log.debug(
                        f"Fulfilled {fulfillments_count} of {requests_count} requests"
                    )

        if seconds_between_checks == 0:
            break

        log.debug(f"Sleeping {seconds_between_checks} seconds until next check")
        time.sleep(seconds_between_checks)

    log.warning("Exiting")
