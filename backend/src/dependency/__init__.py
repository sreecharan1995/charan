"""
This module contains classes used by the dependency microservice implementation.

The dependency microservice api allows to associate packages and bundles to levels, 
in the form of profiles, calculate effective dependencies at a level, list the calculated 
list of packages from bundles at a level (or at a specific profile level), etc.

Calculated package dependencies are fetched for example when a tool script is to be run from
a rez-env and the needed packages are then requested from this service, at the project-level 
at which the triggering event took place.
"""