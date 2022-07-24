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

# TODO

- email preferences for new users: use "only on mention", if possible
