# Gitea API

## Create a Token

    ./create-token.sh

## Register Users

Requires a token and users defined in `users.txt`:

    ./register.sh

## Add Users to a Team

First, figure out which teams exist:

    ./list-teams.sh

Second, take the `id` of the team and add the users in `users.txt` to it:

    ./add-to-team.sh
