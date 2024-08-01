"""
This module contains classes used by the scheduler microservice implementation

The scheduler api allows to receive events from the internel event bus, coming from two sources:

 - The sourcing microservice, which in turn captured the sg webhooks events and augmented them before sending them again
 - The pod entry point when it processes job executions to report progress or rescheduling.

When a reschedule event is received, a new job is created, reusing the previous job id as a prefix to the new job id, whish is
suffized with a -r-xxxxxx were x is a random letter. Also, the newly created job request is marked as being a reschedule from 
a parent job, to help debugging.

When a job progress report event is received (like when the job starts, or finishes), the time stamp marks in the job request
are updated (in dynamo).

In order to schedule job pods in k8, a number of validations take place, like:

 - the job request must be due and be unprepared (never attempted to prepare to run)
 - the k8 job must not exist already (this is checked against k8)
 
This service has two main entry points, one for the fast-api web app and one to run the process which reads data about 
the due job requests and actually schedule jobs to be run in kubernetes job+pods.

Notice that the same event from the same source is always assigned the same job id, to help tracing the job lifecycle
among microservices. Even the k8 jobs and pods created to run it, share the job id as prefix.

Jobs created in k8 lie around for aprox 72 , after that they are cleaned up as well as their pods.
"""