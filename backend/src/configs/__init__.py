"""
This module contains classes used by the configs microservice implementation

The configs microservice api allows to associate configs to levels, calculate effective configurations at a level, 
switch active configurations, etc

Configurations have names. At any level, there can be only one active configuration, for the same name.

This service validates that the level actually exists and that the calling user has access to it.
"""