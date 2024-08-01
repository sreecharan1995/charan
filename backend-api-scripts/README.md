
## HOW TO USE THE BACKEND SCRIPTS ##

This command-line scripts are organized by application. So please first change your 
current directory to one the folders below spin_microservices/backend-api-scripts/

For example:

	```
	$ cd backend-api-scripts/
	$ cd configs/
        ```

Most backend endpoint require an authentication token to work. Once you have a token
create a file named .api.token and inlude the token itself as this file content.

For example:

	```
	$ cp ~/Downloads/latest.token.txt .api.token
	```

Once the token is in place you are able to use one of the available scripts under the 
application folder.

For example, for configs/ these are some of the scripts:

	```
	create-configs
	delete-configs-x
	get-configs
	get-configs-x
	patch-configs-x
	update-configs-x-status
	```

Before calling any of those executables, you may want to specify the environment you will
be connecting to. 

For example a local development application backend, the remote UAT
backend or the remote DEV backend. That is accomplished by calling one of the following to
switch the backend option:

	```
	./backend local
	./backend uat
	./backend dev
	```

### Some script usage examples follow ###

Perform HTTP GET method call to the endpoint `/configs` to list configurations:

	```
	./get-configs
	```

Perform HTTP GET method call to endpoint `/configs?path=/Mumbai&name=basic&p=3`

	```
	./get-configs 'path=/Mumbai&name=basic&p=3'
	```

Perform HTTP POST method call to endpoint `/configs` using the json at `data/config0.json` as body to 
create a config:

	```
	./create-configs data/config0.json
	```

Perform a HTTP PUT method call to `/configs/x/status` replacing `x` with `cid_lg8qg8jcco59fanq55cnsce5` and
using the content of `data/current.false.json` as body:

	```	
	./update-configs-x-status  cid_lg8qg8jcco59fanq55cnsce5 data/current.false.json
	```

Perform a HTTP DELETE method call to `/configs/x` replacing `x` with `cid_lg8qg8jcco59fanq55cnsce5` to 
delete a config:

	```
	./delete-configs-x cid_lg8qg8jcco59fanq55cnsce5
	```

### Examples using sourcing endpoints ###

First move into `backend-api-scripts/sourcing`.

Perform a POST to simulate an actual event as if it were incoming after a shotgrid webhook sends it:

	```
	./post-on--event data/event.sample.sg.1.json
	```

### Examples using scheduler endpoints ###

First move into `backend-api-scripts/scheduler`.

Perform a POST requesting to "reset a job request". This will make the scheduler exec to re-process a job which has already 
been prepared or run inside a k8 pod, as if it were new. However its due_ns timestamp will be kept unchanged:

	```
	./post-resetjob-x jog-sg-45335-5334-0
	```

Perform a POST of an event, to simulate an actual event as sent from the sourcing microservice 
via the aws event bus:

	```
	./post-on--event data/event.sample.esrc.1.json
	```

Perform a POST of an event, to simulate an actual event as sent by the k8 pod when for example, 
reports a job progress or as in this case, to ask a job to be rescheduled as a new (cloned) job:

	```
	./post-on--job--event data/event.reschedule.1.json
	```

Other misc scripts are provided as were helpful during development, like the case of

	```
	./get-k8-jobs
	```

but this endpoints should be disabled in production.

### Adding new scripts ###

The scripts logic is already implemented, the name indicates which endpoint to call, where to use the arg 
replacements, token usage and so on.. For example, if a new GET-method-callable endpoint is available at
`/trees/{id}/comments/{id}` use any other on-liner script like `get-configs` as a template and put a proper name:

	```
	cp get-configs get-trees-x-comments-x
	```

That way it may be called with two arguments, like this:

	```
	./get-trees-x-comments-x tree_121 comment_987
	```

to produce an HTTP GET method call to endpoint `/trees/tree_121/comments/comment_987`

Notice the first word is 'get', so it produces a `GET` method call, but some other words are mapped 
conveniently, like `create` which produces a `POST`, or `update` that produces a `PUT`, or `list` which
also produces a `GET`

Check the names of other scripts in other app folders to see more examples.

Also notice that on each app folder there is a `data/` directory containig some json data files that 
may be helpful for some app use cases.

