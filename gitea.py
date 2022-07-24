#!/usr/bin/env python3

import json

import click
import requests


@click.group(help='Access the Gitea API.')
@click.option('--token-file', default='.token')
@click.option('--base-url', default='https://code.frickelbude.ch/api/v1')
@click.pass_context
def cli(ctx, token_file, base_url):
    ctx.ensure_object(dict)
    ctx.obj['TOKEN_FILE'] = token_file
    ctx.obj['BASE_URL'] = base_url


@cli.command(help='Create a new token')
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--token-name', default='api-token')
@click.pass_context
def new_token(ctx, username, password, token_name):
    session = requests.Session()
    session.auth = (username, password)
    base_url = ctx.obj['BASE_URL']
    token_file = ctx.obj['TOKEN_FILE']
    url = f'{base_url}/users/{username}/tokens'
    headers = {'Content-Type': 'application/json'}
    res = session.post(url, json={'name': token_name}, headers=headers)
    if res.status_code == 201:
        with open(token_file, 'w') as f:
            f.write(res.json()['sha1'])


@cli.command(help='List all organizations')
@click.pass_context
def list_orgs(ctx):
    print(http_get(ctx, 'admin/orgs').json())


@cli.command(help='List all teams of an organization')
@click.option('--org')
@click.pass_context
def list_teams(ctx, org):
    print(http_get(ctx, f'orgs/{org}/teams').json())


def http_get(ctx, endpoint, accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    token_file = ctx.obj['TOKEN_FILE']
    url = f'{base_url}/{endpoint}'
    with open(token_file, 'r') as f:
        token = f.read().strip()
    headers = {
        'Accept': accept,
        'Authorization': f'token {token}',
    }
    return requests.get(url, headers=headers)


if __name__ == '__main__':
    cli()
