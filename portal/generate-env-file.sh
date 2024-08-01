#!/usr/bin/env bash

function replace_env_var()
{
  sed -i "s|$1|$2|g" .env.local.prod
}

# Build info
echo $BUILD_ID
replace_env_var "%BUILD_ID%" "$BITBUCKET_BUILD_NUMBER"

export TZ='America/Toronto'
BUILD_DATETIME=$(date +"%Y-%m-%d %T %Z")
replace_env_var "%BUILD_DATE%" "$BUILD_DATETIME"

replace_env_var "%BUILD_HASH%" "$BITBUCKET_COMMIT"

BUILD_LINK="https:\/\/bitbucket.org\/$BITBUCKET_REPO_FULL_NAME\/pipelines\/results\/$BITBUCKET_BUILD_NUMBER"
replace_env_var "%BUILD_LINK%" "$BUILD_LINK"

# Rename to .env.local.prod to .env.local to load in App  
mv .env.local.prod .env.local