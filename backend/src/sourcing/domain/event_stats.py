from typing import Dict, Tuple
import datetime
from common.build_settings import BuildSettings
import threading

build_settings: BuildSettings = BuildSettings()

lock = threading.RLock()

class EventStats():
    """Represents stats regarding event types, like counters
    """

    _all_counts: Dict[int,Dict[str,int]] = dict() # [minute,[type,count]]
    _last_minute: int = -1

    def __init__(self) -> None:
        pass

    def increment(self, event_type: str) -> None:

        lock.acquire()

        event_type = event_type.lower().strip()

        current_minute: int = datetime.datetime.now().minute

        if self._last_minute != current_minute:
            self._all_counts[current_minute] = dict()
            self._last_minute = current_minute

        current_minute_counts: Dict[str,int] = self._all_counts[current_minute]

        type_count: int = current_minute_counts.get(event_type, 0)

        current_minute_counts[event_type] = type_count + 1

        lock.release()

    def counts(self) -> Tuple[int, Dict[str, int]]:

        lock.acquire()

        total_counts: Dict[str,int] = dict()

        for d in self._all_counts.values(): # iterate over each dict (the dict kept for each minute)
            for event_type, event_count in d.items(): # iterate over the event types and its counts stored on that minute dict
                total_for_event: int = total_counts.get(event_type, 0) # get the current total for the event type
                total_counts[event_type] = total_for_event + event_count # increas the current total with the stored count on the minute for the event type

        total: int = sum(c for c in total_counts.values())

        to_return = total, total_counts  # return sum and dict with totals for each event type

        lock.release()

        return to_return




            

        
