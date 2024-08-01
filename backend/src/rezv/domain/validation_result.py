import io
from typing import Any, Dict, Optional

from rez.exceptions import RezError  # type: ignore
from rez.resolved_context import ResolvedContext  # type: ignore
from rezv.domain.validation_request import ValidationRequest
from rezv.rez_settings import RezSettings


class ValidationResult:
    def __init__(
        self,
        request: ValidationRequest,
        resolved_context: Optional[ResolvedContext] = None,
        exception: Optional[RezError] = None,
    ):
        self.request = request
        self.resolved_context = resolved_context
        self.exception = exception
        self.settings = RezSettings.load()

    def get_message(self) -> Dict[Any, Any]:

        profile_id: str = self.request.get_id()

        message = {
            "in_response_to_event": self.request.get_event_id(),
            "type": self.request.get_detail_type(),
            "id": profile_id,
        }

        if self.exception is not None:
            message["validation_result"] = "Invalid"
            message["result_reason"] = str(self.exception)
        else:
            if self.resolved_context is not None:
                message["validation_result"] = "Valid" if self.resolved_context.success else "Invalid"  # type: ignore
                output = io.StringIO()
                self.resolved_context.write_to_buffer(output)  # type: ignore # TBI: write directly to file instead of buffer
                message["result_reason"] = str(self.resolved_context)
                rxt_filepath: Optional[str] = self.settings.new_rxt_path(profile_id)
                if rxt_filepath is not None:
                    rxt: str = output.getvalue()
                    f = open(rxt_filepath, "w")
                    f.write(rxt)
                    output.close()
                    f.close()
                message["rxt"] = rxt_filepath
            pass

        return message
