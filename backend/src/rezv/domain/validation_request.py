from typing import Any, Dict, List


class ValidationRequestException(Exception):
    pass


class ValidationRequest:
    """
        {
      "version": "0",
      "id": "b0f986e6-93f9-ef78-f8e1-d9f029e5b0a9",
      "detail-type": "profile-validation-request",
      "source": "dependency-service",
      "account": "301653940240",
      "time": "2022-07-12T18:42:50Z",
      "region": "us-east-1",
      "resources": [],
      "detail": {
        "id": "profile_drbrhqekihmx",
        "path": "/",
        "name": "root",
        "description": "root profile",
        "created_at": "2022-Jul-12T18:42:50",
        "profile_status": "pending",
        "packages": [],
        "bundles": [],
        "comments": []
      }
    }
    """

    def __init__(self, event: Dict[Any, Any]):

        if (
            event.get("detail-type") != "profile-validation-request"
            and event.get("detail-type") != "bundle-validation-request"
        ):
            raise ValidationRequestException("Unexpected detail-type")

        event_detail = event.get("detail")

        if event_detail is None:
            raise ValidationRequestException("Missing detail")
        elif event_detail.get("id") is None:
            raise ValidationRequestException(
                f"Missing id for {event_detail.get('type')}"
            )

        self.event = event

    def get_packages(self):
        return self.event["detail"]["packages"]

    def get_bundles(self) -> List[Any]:
        if self.event["detail"]["bundles"] is not None:
            return self.event["detail"]["bundles"]
        else:
            return []

    def get_event_id(self):
        return self.event["id"]

    def get_id(self):
        return self.event["detail"]["id"]

    def get_detail_type(self):
        return self.event.get("detail-type")
