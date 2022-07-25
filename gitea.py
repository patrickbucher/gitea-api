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


@cli.command(help='List all repos of a user')
@click.option('--username')
@click.pass_context
def list_repos(ctx, username):
    print(http_get(ctx, f'users/{username}/repos').json())


@cli.command(help='Delete a user by its username with all owned repos')
@click.option('--name')
@click.pass_context
def delete_user(ctx, name):
    repos = http_get(ctx, f'users/{name}/repos').json()
    owned = filter(lambda r: r.get('owner', {}).get('login', '') == name, repos)
    names = map(lambda r: r.get('name', ''), owned)
    for repo in names:
        print(f'delete {repo} of {name}')
        print(http_delete(ctx, f'repos/{name}/{repo}'))
    orgs = http_get(ctx, f'users/{name}/orgs').json()
    org_names = map(lambda o: o.get('username', ''), orgs)
    for org_name in org_names:
        print(f'remove {name} from {org_name}')
        print(http_delete(ctx, f'orgs/{org_name}/members/{name}'))
    print(http_delete(ctx, f'admin/users/{name}'))


@cli.command(help='Delete all users except the one authenticated')
@click.pass_context
def delete_users(ctx):
    keep = http_get(ctx, 'user').json()
    users = http_get(ctx, 'admin/users').json()
    def same_user(a, b):
        return a['id'] == b['id'] and a['login'] == b['login']
    to_delete = filter(lambda u: not same_user(u, keep), users)
    for user in to_delete:
        ctx.invoke(delete_user, name=user['login'])


def http_get(ctx, endpoint, accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Accept'] = accept
    return requests.get(url, headers=headers)


def http_delete(ctx, endpoint, accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Accept'] = accept
    return requests.delete(url, headers=headers)


def get_auth_header(ctx):
    token_file = ctx.obj['TOKEN_FILE']
    with open(token_file, 'r') as f:
        token = f.read().strip()
        return {'Authorization': f'token {token}'}


if __name__ == '__main__':
    cli()
