# Gitea API

Some Python (3.10) scripts to access the Gitea API, using the
[click](https://pypi.org/project/click/) and
[requests](https://pypi.org/project/requests/) libraries.

## Setup

Create a virtual environment, and activate it:

    $ python -m venv env
    $ . env/bin/activate

Install the dependencies:

    $ pip install -r requirements.txt

Generate a token for your Gitea profile and store it under `.token`, or create a
new one:

    $ ./gitea.py new-token --username patrick --password [prompted if missing]

Show help:

    $ ./gitea.py --help

### Bulk Registration

Create a YAML file for bulk registration (`bulk-registration.yaml`):

```yaml
teams:
  - teamname: alligators
    description: Team Alligators
    users:
      - username: rudi_loehlein
        fullname: Rudi Löhlein
        email: patrick.bucher87+rudi_loehlein@gmail.com
      - username: mai_ling
        fullname: Mai Ling
        email: patrick.bucher87+mai_ling@gmail.com
  - teamname: badgers
    description: Team Badgers
    users:
      - username: john_doe
        fullname: John Doe
        email: patrick.bucher87+john_doe@gmail.com
      - username: jane_done
        fullname: Jane Done
        email: patrick.bucher87+jane_done@gmail.com
```

Using the `bulk-register` command, and a given organization name (`--org`):

    $ ./gitea.py bulk-register --org demo --bulkfile bulk-registrations.yaml

The following steps are performed:

1. Each listed team is created with the given parameters, and added to the given
   organization.
2. Each listed user is created with the given parameters, and added to the team.

So a user belongs to exactly one team.

# TODO

- email preferences for new users: use "only on mention", if possible
  - alternative: via database using `update "user" set email_notifications_preference = 'onmention';`

## CSV to YAML

To convert CSV data (exported by the school administration tool) to YAML, use the following command:

```bash
./csv-to-yaml.py --name inf22a --description S-INF22aL inf22a.csv inf22a.yaml
```