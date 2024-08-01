class MockedEvent:
    """Represents an event sent to a mocked internal "bus".

    This instances are created during local development or tests where there is no need to actually send events to actual buses.
    """

    bus_name: str
    event_type: str
    payload: str

    def __init__(self, bus_name: str, event_type: str, payload: str):

        self.bus_name = bus_name
        self.event_type = event_type
        self.payload = payload

    def str(self) -> str:
        return f"bus = {self.bus_name}, event_type = {self.event_type}, payload = {self.payload}"
