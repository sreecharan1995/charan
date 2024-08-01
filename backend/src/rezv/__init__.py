"""
This module contains classes used by the rezv microservice implementation.

The rez service main function is to receive validation requests from the dependency microservice.

After producing a response based on rez-env it thens triggers validation events pushed to the internal event bus
so the dependency service can receive them back and update the profiles regarding their validated state.
"""