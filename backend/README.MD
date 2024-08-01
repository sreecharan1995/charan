# Setting up local environment
## Tools that will be needed
1. [Pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)

## Readying the local environment
1. Create file .env at the root of the backend directory.
2. Copy content of .env.sample into the new .env file
3. Replace values with ??? with real values. For reference see [here](https://dependencies.dev.spinvfx.com/pdocs/?search=settings).

## Running the different services
All builds, local or otherwise, happen through pipenv. The Pipfile is the one that defines all dependencies for runtime and development.
In the Pipfile you will also find a set of commands to run the different services. 

Each one of the services has a corresponding section in the Pipfile that will allow to run in dev mode or production mode, run tests and generate documentation.

In order to run a service execute the following command from the backend directory.

``
pipenv run <script-name>
``

Where <script-name> is one of the scripts found in [Pipfile](Pipfile)
For example, to run the dependency service in dev mode execute:

``
pipenv run dependency-server-dev
``
# DynamoDB

Tables in DynamoDB are named in the following manner:

``<prefix>-<table-name>``

Each service defines the names of the tables it needs. The prefix is globally driven by property:

``DYNAMODB_TABLES_USERID``

When deploying to an environment, this variable takes the name of the environment. When running locally, the variable should take a unique value associated to the user.
This is in order to avoid to users writing/reading from each other tables.

See specific readmes inside each service for the table names.

All operations directly on DynamoDB (not through the services) should be performed from the AWS console or through the aws-cli.
When clearing a table we have done it before by manually deleting entries from the console. Entries can be deleted in bulk in a page by page manner.

For information and backing up and restoring DynamoDB tables, see [here](https://aws.amazon.com/dynamodb/backup-restore/).

# EventBridge

EventBridge is currently used for communication to/from the rez service. The dependency service posts an event whenever a change is done to a profile.
The REZ service picks it up and validates the profile. When done, the REZ services posts the result of the validation back to the bus.

Messages are sent to the bus using the official AWS python API [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)

In the bus, messages are routed to different targets using rules. The rules indicate what target(s) a message that matches a certain expression should be routed to. 

Both services, REZ and SWDS receive messages from the bus via http. These targets are defined and managed as part of 
the infrastructure via terraform.

