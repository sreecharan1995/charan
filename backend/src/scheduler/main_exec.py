# coding: utf-8

import time
from common.logger import log
from scheduler.scheduler_settings import SchedulerSettings
from scheduler.service.aws.scheduler_ddb import SchedulerDdb
from scheduler.service.scheduler_service import SchedulerService

"""
    Scheduler exec process

    This process is the one that picks up job requests and schedules them as kubernetes jobs

    This is an entry point for the scheduler exec application.
"""

if __name__ == '__main__':

    log.info("Running in mode 'scheduler exec'")

    settings: SchedulerSettings = SchedulerSettings.load()

    levels_ddb = SchedulerDdb(settings=settings)

    if not levels_ddb.create_tables():
        log.warning("Initialization failed")
        exit(1)


    scheduler_service: SchedulerService = SchedulerService(settings)

    seconds_between_checks: int = settings.ESCH_JOBREQUEST_RECHECK_WAIT

    log.info(
        f"Configured to wait {seconds_between_checks} seconds before checking again for new job requests"
    )

    while True:

        try:    
            scheduler_service.process_due_job_requests()
        except BaseException as be:
            log.error(f"Unexpected error during iteration. {be}")
        
        if seconds_between_checks == 0:
            break

        scheduler_service.update_health_tracking_file()

        log.debug(f"Sleeping {seconds_between_checks} seconds until next check")
        time.sleep(seconds_between_checks)

    log.warning("Exiting")
