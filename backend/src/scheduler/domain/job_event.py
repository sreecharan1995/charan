from typing import Dict, Any, Optional

class JobEvent():
    """Represents job progress event data.

    These events are signaled for example from the k8 job pods running the "tapi" image before and after the tool is run.
    """

    job_id: Optional[str] # used always
    started_at: Optional[str] # used when starting
    finished_at: Optional[str] # used when finishing
    due_at: Optional[str] # used when recheduling
    exit_code: Optional[str] # used when finishing
    
    def __init__(self):
            pass
    
    @staticmethod
    def from_dict(detail: Dict[str,Any])-> 'JobEvent':
          
          job_event: JobEvent = JobEvent()

          job_event.job_id = detail.get("job_id", None)
          job_event.due_at = detail.get("due_at", None)          
          job_event.started_at = detail.get("started_at", None)          
          job_event.finished_at = detail.get("finished_at", None)
          job_event.exit_code = detail.get("exit_code", None)

          return job_event

    def is_reschedule_event(self) -> bool:
          return self.job_id is not None and len(self.job_id) > 0 and \
            self.due_at is not None and self.finished_at is None and self.exit_code is None and self.started_at is None

    def is_started_event(self) -> bool:
          return self.job_id is not None and len(self.job_id) > 0 and \
            self.started_at is not None and self.finished_at is None and self.exit_code is None and self.due_at is None
    
    def is_finished_event(self) -> bool:
          return self.job_id is not None and len(self.job_id) > 0 and \
            self.finished_at is not None and self.started_at is None and self.exit_code is not None and self.due_at is None


# started:   { "job_id": "", "started_at": "" }
# finished:  { "job_id": "", "finished_at": "", "exit_code": "" }
