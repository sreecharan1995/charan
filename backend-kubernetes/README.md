Each backend service has its own folder for kubernetes configuration.
We use [kustomize](https://kustomize.io/) to generalize resources while leaving environment specifics for runtime sustitutions.
For a full explanation of the folder structure and how substitutions happen, read [here](https://kubectl.docs.kubernetes.io/guides/).

This guide assumes you have configured the kubernetes cluster in your workstation. If not follow instructions found [here](https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html).

It also assumes you have kubectl installed and have proper credentials to access the k8s cluster.

# How to run kubectl
There is no need to for any of this in the local environment. This guide is only needed to create/update a remote environment.

## Setting up th dependencies service in the dev environment
1. Change directories to backed-kubernetes/dependency/dev
2. Execute the command ``kubectl apply -k .``

Alternatively the command can be run from the root of the backend-kubernetes directory but then you need to provide a specific path. The command would then look like: 

``kubectl apply -f dependency/dev``

## Configuration values
Some configuration values are currently stored as environment variables in bitbucket while other are found in the *.env files inside this folder.

When the build runs in bitbucket, the environment variables are available at runtime and these values are replaced inside the config files for kubernetes using kustomize. 
All currently hardcoded values in these *.env files can be moved to bitbucket environment variables and their values removed from the files in favour of a reference to the environment variable.
An example of how to read variables from bitbucket environment can be seen [here](base/prod/config/aws_dynamodb_secrets.env). 

## Auth configuration
the auth configuration for the dev environment can be found [here](base/dev/config/auth_secrets.env)

Right now the values are hardcoded and this is not a problem as these values are all public.

No secrets are required to setup AAD integration.


