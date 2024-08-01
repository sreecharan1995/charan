# coding: utf-8

from __future__ import annotations
from typing import Dict, Any


class JobRequest:
    """Represents a job request.

    Scheduled job Requests are persisted in dynamodb from scheduler fast api and later retrieved from scheduler exec to spawn new k8 jobs.
    """

    job_id: str
    triggering_event_type: str
    due_ns: int
    tool_config_json: Dict[str,Any]
    event_json: Dict[Any,Any]
    prepared_ns: int
    started_ns: int
    finished_ns: int
    exit_code: int

    def __init__(self,
                 job_id: str,
                 triggering_event_type: str,
                 due_ns: int,
                 tool_config_json: Dict[str,Any],
                 event_json: Dict[Any,Any],
                 prepared_ns: int = 0,
                 started_ns: int = 0,
                 finished_ns: int = 0,
                 exit_code: int = -1):
        self.job_id = job_id
        self.triggering_event_type = triggering_event_type
        self.due_ns = due_ns
        self.tool_config_json = tool_config_json
        self.event_json = event_json
        self.prepared_ns = prepared_ns
        self.started_ns = started_ns
        self.finished_ns = finished_ns
        self.exit_code = exit_code
