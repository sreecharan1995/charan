# Add these lines to .bashrc:

function find_env_source() 
{
	d="$1" # in dir
	f="$(realpath "$d"/env.source)"
	if test -e "$f"
	then
		echo "$f"
	elif ! test -d "$d/.git" && test "$d" != "$HOME" && test "$d" != "/"
	then
		find_env_source "$d/.."
	fi
}

function env_source() 
{
    (
        t="$1"
		s="$(find_env_source "$PWD")"
		if test -n "$s"
		then
			source "$s" "$(dirname "$s")"
		else
			echo "[ENV] WARN: env.source not found" 1>&2		
		fi

		if test "$t" != "${t#/}"
		then
			"$@"
		else
			if test -z "$(type asdf)"
			then
				echo "[ENV] ERROR: asdf not found" 1>&2		
			else
				asdf exec "$@"
			fi
		fi
    )
}

alias terraform='env_source terraform'
alias terraform-docs='env_source terraform-docs'
alias aws='env_source aws'
alias kubectl='env_source kubectl'
alias eksctl='env_source eksctl'
alias k9s='env_source k9s'
alias helm='env_source helm'
alias tfsec='env_source tfsec'
alias lens='env_source /usr/bin/lens'
alias envsubst='env_source /usr/bin/envsubst'
