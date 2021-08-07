#!/usr/bin/bash

token=$(curl -X POST -H 'Content-Type: application/json' -d '{"name": "api-access"}' \
    -u patrick:`pass show gitea-patrick` \
    https://code.frickelbude.ch/api/v1/users/patrick/tokens | jq -r '.sha1')

echo $token > .token
