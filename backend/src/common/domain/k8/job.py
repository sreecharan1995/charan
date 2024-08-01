from typing import Optional
from common.logger import log

class Job():
    """Wrapper for a k8 job data
    """

    name: str
    namespace: str
    status: Optional[str]

    def __init__(self, name: str, namespace: str, status: Optional[str] = None) -> None:

        self.name = name
        self.namespace = namespace
        self.status = status

    def get_status(self) -> str:

        if self.status is None:
            return "unknown"
                
        if self.status.succeeded is not None: # type: ignore
            return "succeeded"
        
        if self.status.failed is not None: # type: ignore            
            return "failed"
        
        if self.status.active is not None: # type: ignore
            return "active"
        
        log.debug(f"(JOB:{self.name} status: {self.status}")

        return "created"

    