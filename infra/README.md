# SETUP # 

## Install asdf and plugins ##

Install `asdf` using the guide at [http://asdf-vm.com/guide/getting-started.html]

After the core asdf is ready and sourced into the shell, install the following plugins:

  * `asdf plugin add  terraform  	https://github.com/Banno/asdf-hashicorp.git`
  * `asdf plugin add  awscli     	https://github.com/MetricMike/asdf-awscli.git`
  * `asdf plugin add  kubectl    	https://github.com/Banno/asdf-kubectl.git` 
  * `asdf plugin add  k9s        	https://github.com/looztra/asdf-k9s.git`
  * `asdf plugin add  helm       	https://github.com/Antiarchitect/asdf-helm.git`
  * `asdf plugin add  eksctl     	https://github.com/elementalvoid/asdf-eksctl.git`
  * `asdf plugin add  tfsec      	https://github.com/woneill/asdf-tfsec.git`
  * `asdf plugin add  terraform-docs	https://github.com/looztra/asdf-terraform-docs.git`
  


From the repository root, where `.tool-versions` file is located, run `asdf install` so
each version of the tools are downloaded.

At this point the executables `terraform`, `aws`, `kubectl`,`eksctl`, `k9s`, etc, are run via `asdf` 
according to the versions specified in `.tool-versions`

To explore other available plugins use: `asdf plugin list all`
To adjust a tool version or add new tools edit the content of `.tool-versions` and re-execute `asdf install`

## Custom env for asdf tools ##

To allow usage of a custom environment per folder and/or per user/host, and to allow asdf tools to 
be aware of this custom environment, there is a mechanism in place, desribed below.

First add the lines of `env.bashrc` to `~/.bashrc` and reload the shell, or temporary source that file
into your current shell. Note at the end of the file that there are aliases for commands like 
`terraform` and `aws`. These aliases use a function that detects and executes the custom env loading logic
before the actual asdf specific tool shim is executed.

To customize the environment, create a file `.env.default`, or `.env.$USER`, or `.env.$USER.$HOSTNAME` and place 
it inside the folder that needs the environment. When a tool is executed via the alias, then ALL 
of the existing environment files will be looked up and sourced into the shell. That will happen in the following order:

  1. `.env.default`
  2. `.env.$USER`
  3. `.env.$USER.$HOSTNAME`

BUT before those are sourced, the same lookup will be done in the parent folder, up to the repository root folder
(where `env.source` file is expected to be found)

Summarizing: env files in parent folders are sourced first, so you can always override env vars in subfolders, and
more general files (like `.env.default`) are sourced before more specific files (like `.env.$USER`).

Files matching `.env.*` are git-ignored (like in `.env.joe`). They may be useful to setup credentials and other 
user-specific values. Take a look into `.env.default` as example.

## terraform tool usage ##

Under the terraform folder, there is a file structure useful to organize and modularize the infraestructure described.

The leaf folders (like `ecr` or `eks`) contains a convenient set of files all describing the same infra resources. For 
example, you can find this files under `ecr/` as well as under `eks/`

      ecr
      ├── backend.tf
      ├── main.tf
      ├── output.tf
      ├── versions.tf

You can change dir into `ecr/` and execute terraform commands to initialize, validate, plan and apply 
infraestructural changes.






