#!/usr/bin/bash

token=$(cat .token)

curl -X GET -H "Accept: application/json" \
    -H "Authorization: token ${token}" \
    https://code.frickelbude.ch/api/v1/user | jq
