#!/usr/bin/bash

token="$(cat .token)"
team="${1}"

if [ -z "${team}" ]
then
    echo "no team ID provided, usage: add-to-team.sh [team ID]"
    exit 1
fi

while read line
do
    name="$(echo $line | cut -d ',' -f 1)"
    email="$(echo $line | cut -d ',' -f 2)"
    username="$(echo $name | tr -cd '[:alpha:]' | tr '[:upper:]' '[:lower:]')"

    echo "add ${name} ${email} ${username} to team ${team}"

    curl -X PUT -H "Accept: application/json" -H "Authorization: token ${token}" \
        "https://code.frickelbude.ch/api/v1/teams/${team}/members/${username}" | jq

done <users.txt
