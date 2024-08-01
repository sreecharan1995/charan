# coding: utf-8

from typing import Dict

from pydantic import BaseModel, Field

class EventStatsModel(BaseModel):
    """Model representing event counts
    """

    events_last_hour: int
    types_last_hour: Dict[str,int] = Field(default={}, title='event counts in the last hour', description='The total number of events and counts per type, in the last hour', example="{}")
        
    @staticmethod
    def from_stats(event_counts: Dict[str,int]) -> 'EventStatsModel':

        model: EventStatsModel = EventStatsModel(events_last_hour=sum(c for c in event_counts.values()), types_last_hour=event_counts)

        return model

EventStatsModel.update_forward_refs()


