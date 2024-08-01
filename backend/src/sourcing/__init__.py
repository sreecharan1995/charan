"""
This module contains classes used by the event sourcing microservice implementation

The sourcing microservice api receives events triggered from webhooks like the ones in shotgrid, in order to augment them
before sending them via the internal event bus. After that, the scheduler microservice receive the augmented event and actually 
execute them after validation is performed.

The sourcing service aims to centralize reception of data incoming from different external services and to translate this data to 
internal events which are then handled by other microservices connected to the bus.

Augmentation include details about the "proxy" agent (this own service) which is re-sending the event to the internal bus.
"""

from sourcing.domain.event_stats import EventStats

event_stats = EventStats()