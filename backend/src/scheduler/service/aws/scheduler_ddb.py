import json
import time
from typing import Any, List, Optional, Dict

from boto3.dynamodb.conditions import Attr, Key  # type: ignore

from common.logger import log
from common.service.aws.base_ddb import BaseDdb
from common.service.aws.ddb_table import DdbTable
from scheduler.domain.job_request import JobRequest
from scheduler.scheduler_settings import SchedulerSettings


class SchedulerDdb(BaseDdb):
    """Provides the methods to operate on the dynamodb table holding data about job requests
    """

    _settings: SchedulerSettings

    TABLE_JOBREQUEST_ALIAS: str = "JOBREQUEST"

    def __init__(self, settings: SchedulerSettings):

        self._level_settings = settings
        
        TABLE_JOBREQUEST = DdbTable(self.TABLE_JOBREQUEST_ALIAS, settings.current_jobrequest_table(),
                                key_schema=[
                                    {
                                        "AttributeName": "job_id",
                                        "KeyType": "HASH"
                                    }
                                ],
                                attr_defs=[
                                    {
                                        "AttributeName": "job_id",
                                        "AttributeType": "S"
                                    },
                                    {
                                        "AttributeName": "catalog",
                                        "AttributeType": "S"
                                    },
                                    {
                                        "AttributeName": "due_ns",
                                        "AttributeType": "N"
                                    },
                                ],
                                global_indexes=[
                                {
                                    'IndexName': 'job_due_ns',
                                    'KeySchema': [
                                        {
                                            'AttributeName': 'catalog',
                                            'KeyType': 'HASH'
                                        },
                                        {
                                            "AttributeName": "due_ns",
                                            "KeyType": "RANGE"
                                        },
                                    ],
                                    'Projection': {
                                        'ProjectionType': 'ALL'
                                    },
                                    'ProvisionedThroughput' :{
                                        'ReadCapacityUnits': 5,
                                        'WriteCapacityUnits': 5,
                                    }
                                }
                                ],
                                read_capacity=5,
                                write_capacity=5)

        super(SchedulerDdb, self).__init__(settings,
                                        ddb_tables=[TABLE_JOBREQUEST])

    def table_jobrequest(self):
        return super().ddb_table(self.TABLE_JOBREQUEST_ALIAS)

    def get_job_request(self, job_id: str)-> Optional[JobRequest]:

        dict: Optional[Dict[Any,Any]] = self.__get_job_request(job_id)

        if dict is None:
            return None
        
        return self._job_request_from_dict(dict)        

    def _job_request_from_dict(self, dict: Dict[Any,Any])-> JobRequest:

        return JobRequest(
                    job_id=dict.get("job_id", ""),
                    triggering_event_type=dict.get("triggering_event_type", ""),
                    due_ns=dict.get("due_ns", 0),
                    tool_config_json=dict.get("tool_config_json", {}),
                    event_json=dict.get("event_json", {}),
                    prepared_ns=dict.get("prepared_ns", 0),
                    started_ns=dict.get("started_ns", 0),
                    finished_ns=dict.get("finished_ns", 0),
                    exit_code=dict.get("exit_code", -1)
                )    
        
    def new_job_request(self, job_id: str, due_ns: Optional[int], triggering_event_type: str,
                        tool_config_json: Dict[str,Any], event_json: Dict[Any,Any], scheduled_by_job: Optional[str] = None) -> Optional[JobRequest]:

        table = self.table_jobrequest()

        now_ns: int = time.time_ns()

        response = table.put_item(
            Item={
                "catalog": "global", # TODO: from config
                "job_id": job_id, # this job id
                "triggering_event_type": triggering_event_type, # type of event triggering the job (tool config is according to this event type)
                "registered_ns": now_ns,  # this is a ns timestamp for the moment the request was registered
                "due_ns": due_ns if due_ns is not None else now_ns, # if no due time specified, the current time is used (matching registered_ns)
                "tool_config_json": tool_config_json, # serialized json config (matched for the triggering event type) (to be used during tool execution)
                "event_json": event_json, # serialized event data (to be used during tool execution)
                "prepared_ns": 0,  # zero means not yet prepared (or unable to mark as prepared)
                "started_ns": 0,  # zero means not yet started (or unable to mark as started)
                "finished_ns": 0,  # zero means not yet finished (or never marked as finished)
                "exit_code": -1, # negative means no exit code availabe (never finished or never marked as finished), non zero is the exit code of process
                "scheduled_by_job_id": scheduled_by_job or ""
            },
            ConditionExpression='attribute_not_exists(job_id)'
        )

        retries_left: int = 3

        while (
                retries_left > 0
        ):  # deal with fetches not yet returning a successfully created item

            job_request: Optional[JobRequest] = self.get_job_request(job_id)

            if job_request is None:
                log.warning(
                    f"Created job request but still missing. job_id: '{job_id}'. response: '{json.dumps(response)}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return job_request

        return None

    def __get_job_request(self, job_id: str) -> Optional[Dict[Any,Any]]:

        table = self.table_jobrequest()

        response = table.get_item(
            Key={
                "job_id": job_id                
            })  

        dict: Optional[Any] = response.get("Item")  # type: ignore

        return dict
    
    def get_due_job_requests(self) -> Optional[List[JobRequest]]:

        table = self.table_jobrequest()

        now_ns: int = time.time_ns()

        try:
            response = table.query(  # type: ignore                
                IndexName="job_due_ns",
                KeyConditionExpression=Key('catalog').eq('global') & Key('due_ns').lt(now_ns), # type: ignore # & Key('started_ns').eq(0) # type: ignore TODO: read cataglog from config
                FilterExpression=Attr("prepared_ns").eq(0) # type: ignore
            )
        except Exception as e:
            log.error(e)
            return None

        items: Optional[List[Any]] = response.get("Items")  # type: ignore

        if items is None:
            return None
                
        return list(
            map(
                lambda i: self._job_request_from_dict(i), 
                                     items))


    def update_job_as_unprepared(self, job_id: str) -> Optional[bool]:
        
        table = self.table_jobrequest()

        update_expression: str = "set prepared_ns=:prepared_ns, started_ns=:started_ns, finished_ns=:finished_ns, exit_code=:exit_code"
        expression_attr_values: Dict[str,Any] = {":prepared_ns": 0, ":started_ns": 0, ":finished_ns": 0, ":exit_code": -1}

        try:

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attr_values,
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return True if response["Attributes"][
                "prepared_ns"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as unprepared: {e}")
            return None

    def update_job_as_prepared(self, job_id: str, prepared_ns: Optional[int] = None) -> Optional[int]:
        
        table = self.table_jobrequest()

        try:

            prepared_at: int = prepared_ns or time.time_ns()

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression="set prepared_ns=:prepared_ns",
                ExpressionAttributeValues={":prepared_ns": prepared_at},
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return prepared_at if response["Attributes"][
                "prepared_ns"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as prepared: {e}")
            return None
        
    def update_job_as_unrecoverable(self, job_id: str) -> Optional[int]:
        
        table = self.table_jobrequest()

        try:

            prepared_at: int = -1 * time.time_ns()  # use the timestamp, but negative to means unrecoverable preparation error

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression="set prepared_ns=:prepared_ns",
                ExpressionAttributeValues={":prepared_ns": prepared_at}, # when negative means unrecoverable error during preparation
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return prepared_at if response["Attributes"][
                "prepared_ns"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as unrecoverable: {e}")
            return None        

    def update_job_as_started(self, job_id: str, started_ns: Optional[int] = None) -> Optional[int]:
        
        table = self.table_jobrequest()

        try:

            started_at = started_ns or time.time_ns()

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression="set started_ns=:started_ns",
                ExpressionAttributeValues={":started_ns": started_at},
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return started_at if response["Attributes"][
                "started_ns"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as started: {e}")
            return None

    def update_job_as_finished(self, job_id: str, exit_code: int, finished_ns: Optional[int] = None) -> Optional[int]:
        
        table = self.table_jobrequest()
        
        try:

            finished_at: int = finished_ns or time.time_ns()

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression="set finished_ns=:finished_ns, exit_code=:exit_code",
                ExpressionAttributeValues={":finished_ns": finished_at, ":exit_code": exit_code},
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return finished_at if response["Attributes"]["finished_ns"] is not None and response["Attributes"]["exit_code"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as finished (exitcode {exit_code}): {e}")
            return None

    def update_job_as_errored(self, job_id: str) -> Optional[int]:
        
        table = self.table_jobrequest()
        
        try:

            finished_at: int = -1 * time.time_ns()  # a negative value means it finished before started due to unable to start tool

            response = table.update_item(  # type: ignore
                Key={"job_id": job_id},
                UpdateExpression="set finished_ns=:finished_ns",
                ExpressionAttributeValues={":finished_ns": finished_at}, # negative value to signal error before tool started
                ReturnValues="ALL_NEW",
                ConditionExpression='attribute_exists(job_id)'
            )

            return finished_at if response["Attributes"]["finished_ns"] is not None else None

        except Exception as e:

            log.error(f"(JOB:{job_id}) request: failed to mark as tool errored: {e}")
            return None
