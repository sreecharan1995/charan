# This file hold some constants referring to names of the sources when triggering or receiving events from different actors,
# mainly sent or received from sg webhooks or aws event buses.

EB_EVENT_SOURCE: str = "EB"  # generic name for AWS event bus source

EB_EVENT_SOURCE_SOURCING_SERVICE: str = "sourcing-service"
EB_EVENT_SOURCE_VALIDATION_SERVICE: str = "dependency-service"
EB_EVENT_SOURCE_REZ_SERVICE: str = "rez-service"
EB_EVENT_SOURCE_SCHEDULER: str = "scheduler-service"
EB_EVENT_SOURCE_SCHEDULER_JOB: str = "scheduler-job"

SG_EVENT_SOURCE: str = "sg" # used to identify events coming from SG webhooks