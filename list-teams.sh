#!/usr/bin/bash

token=$(cat .token)
organization="${1}"

if [ -z "${organization}" ]
then
    echo "no organization given, usage: list-teams.sh [organization name]"
    exit 1
fi

curl -X GET -H "Accept: application/json" \
    -H "Authorization: token ${token}" \
    "https://code.frickelbude.ch/api/v1/orgs/${organization}/teams" | jq
