"""
This module contains classes used by the levels microservice implementation.

The level service allow to represent a hierarchy of levels mimicking (but augmenting) the shotgrid-like structure
of projects, divisions, asset types, sequences, shots, etc.

Each level can be mapped to a path representation, and a path representation can be expressed also as a json dictionary.

This service has two main entry points, one for the fast-api web app and one to run the process which reads data from
shotgrid and updates the local structures to be in sync.
"""

__pdoc__ = {'main_health': False}

