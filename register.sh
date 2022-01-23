#!/usr/bin/bash

token="$(cat .token)"

while read line
do
    name="$(echo $line | cut -d ',' -f 1)"
    email="$(echo $line | cut -d ',' -f 2)"
    username="$(echo $name | tr -d '[:space:]' | tr -d '[:punct:]' | tr '[:upper:]' '[:lower:]')"
    password="$(pwgen -n 24 1)"

    echo "create account for ${name} ${email} ${username}"

    cat <<EOF >user.json
{
    "email": "${email}",
    "full_name": "${name}",
    "login_name": "${username}",
    "must_change_password": true,
    "password": "${password}",
    "send_notify": true,
    "source_id": 0,
    "username": "${username}"
}
EOF

    curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" -d @user.json \
        -H "Authorization: token ${token}" https://code.frickelbude.ch/api/v1/admin/users | jq

done <users.txt

rm user.json
