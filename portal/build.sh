#!/usr/bin/env bash

echo "executing... npm install"
npm install # Installs all dependencies
echo "executing... rm -rf .next out"
rm -rf .next out # Remove built directories from previous builds (prevent EXIST error)
## build the image
export BITBUCKET_COMMIT_SHORT=$(echo $BITBUCKET_COMMIT | cut -c1-7)
echo "executing... docker build web-portal ."
docker build -t web-portal .
