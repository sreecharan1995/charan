"""Under this src/ folder there are a number of python modules grouping code for each of 
the spinvfx microservices, or code shared by them.

Summarized role of each microservice:

 - levels: api to access shotgrid projects element representations as paths (or named tree levels), a local tree is kept in sync with sg data

 - configs: api to associate configurations to levels

 - dependency: api to associate packages and bundles to levels

 - sourcing: api receiving external data from shotgrid webhooks and possibly others to augment them and push as events in the internal event bus

 - scheduler: api receiving augmented events from the internal bus and executing configured event tools as k8 jobs in rez enviroments setups using the calculated level dependencies

 - rezv: api receiving profile validation requests (from dependencies service for example) and triggering validation results back to the internal bus

"""
