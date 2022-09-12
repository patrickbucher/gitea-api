#!/usr/bin/env python3

from datetime import datetime
from datetime import timezone
import secrets
import string
from zoneinfo import ZoneInfo

import click
import requests
import yaml

cet = ZoneInfo('Europe/Zurich')


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
    owned = filter(lambda r: r.get('owner', {}).get('login', '') == name,
                   repos)
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


@cli.command(help='Delete all the teams of a given organization')
@click.option('--org')
@click.option('--delete-owner-team', is_flag=True)
@click.pass_context
def delete_org_teams(ctx, org, delete_owner_team):
    teams = http_get(ctx, f'orgs/{org}/teams').json()
    for team in teams:
        name = team['name']
        if name == 'Owners' and not delete_owner_team:
            continue
        team_id = team['id']
        print(f'delete team {name} from org {org}')
        print(http_delete(ctx, f'teams/{team_id}'))


@cli.command(help='Delete the given organization with all repos')
@click.option('--org')
@click.pass_context
def delete_org(ctx, org):
    repos = http_get(ctx, f'orgs/{org}/repos').json()
    owned = filter(lambda r: r.get('owner', {}).get('login', '') == org, repos)
    names = map(lambda r: r.get('name', ''), owned)
    for repo in names:
        print(f'delete {repo} of {org}')
        print(http_delete(ctx, f'repos/{org}/{repo}'))
    print(http_delete(ctx, f'orgs/{org}'))


@cli.command(help='Registers all the teams with users to a given organization')
@click.option('--org')
@click.option('--bulkfile', type=click.File('r'))
@click.option('--no-notify', is_flag=True, help='Do not send notification email')
@click.pass_context
def bulk_register(ctx, org, bulkfile, no_notify):
    data = yaml.load(bulkfile.read(), Loader=yaml.SafeLoader)

    assert http_get(ctx, f'orgs/{org}').status_code == 200

    for team_entry in data.get('teams', {}):
        teamname = team_entry['teamname']
        new_team = {
            'name': teamname,
            'description': team_entry['description'],
            'permission': 'read',
            'units': [
                'repo.code',
                'repo.issues',
                'repo.pulls',
                'repo.releases',
            ],
            'includes_all_repositories': True,
        }
        res = http_post(ctx, f'orgs/{org}/teams', new_team)
        if res.status_code != 201:
            print(f'create team "{teamname}" failed: {res.status_code}')
            continue
        else:
            print(f'created team "{teamname}"')
        team_id = res.json().get('id', 0)

        for user_entry in team_entry.get('users', []):
            username = user_entry['username']
            fullname = user_entry['fullname']
            email = user_entry['email']
            register_user(ctx, username, fullname, email, not no_notify)
            add_user_to_team(ctx, username, team_id)


@cli.command(help='Sets team reading permission for code, issues, pull-requests and releases')
@click.option('--org')
@click.pass_context
def set_team_read_rights(ctx, org):
    teams = http_get(ctx, f'orgs/{org}/teams').json()
    team_ids = [t['id'] for t in teams if t['name'] != 'Owners']
    units_map = {f'repo.{scope}': 'read'
                 for scope in ['code', 'issues', 'pulls', 'releases']}
    payload = {
        'units_map': units_map,
        'includes_all_repositories': True,
        'permission': 'read'
    }
    for id in team_ids:
        res = http_patch(ctx, f'teams/{id}', payload)
        if res.status_code != 200:
            print(f'set team {id} read rights failed: {res.status_code}')
        else:
            print(f'set team {id} read rights to read')


@cli.command(help='Lists the forks of a team for a repository')
@click.option('--owner')
@click.option('--repo')
@click.option('--team')
@click.pass_context
def list_forks(ctx, owner, repo, team):
    team_usernames = fetch_team_usernames(ctx, owner, team)
    forks = []
    page_size = 30
    page = 1
    while True:
        fs = http_get(ctx, f'repos/{owner}/{repo}/forks',
                      params={'limit': page_size, 'page': page}).json()

        forks.extend(fs)
        if len(fs) < page_size:
            break
        page += 1

    user_forks = {f.get('owner', {}).get('login', ''): f for f in forks}
    team_forks = {k: v for k, v in user_forks.items() if k in team_usernames}
    tardies = [u for u in team_usernames if u not in team_forks]

    print(f'{"username":30s} {"updated":17s} fork')
    print(f'{"--------":30s} {"-------":17s} ----')
    for u, f in team_forks.items():
        updated = f.get('updated_at', '')
        if updated:
            updated = to_cet_datetime(updated)
        html_url = f.get('html_url', '')
        print(f'{u:30s} {updated:17s} {html_url}')
    for t in tardies:
        print(f'{t:30s} {"never":17s} -')

    n_forks = len(team_forks)
    n_fail = len(tardies)
    print('\nSummary:')
    print(f'{n_forks:2d} forks OK')
    print(f'{n_fail:2d} forks MISSING')
    if n_fail == 0:
        print(f'The members of {team} made their homework!')
    else:
        print(f'The members of {team} have unfinished business!')


@cli.command(help='Lists the pull requests of a team for a repository')
@click.option('--owner')
@click.option('--repo')
@click.option('--team')
@click.pass_context
def list_pull_requests(ctx, owner, repo, team):
    team_usernames = fetch_team_usernames(ctx, owner, team)
    pull_requests = []
    page_size = 30
    page = 1
    while True:
        prs = http_get(ctx, f'repos/{owner}/{repo}/pulls',
                       params={'state': 'all', 'sort': 'recentupdate',
                               'limit': page_size, 'page': page}).json()
        pull_requests.extend(prs)
        if len(prs) < page_size:
            break
        page += 1

    user_prs = {p.get('user', {}).get('login', {}): p for p in pull_requests}
    team_prs = {k: v for k, v in user_prs.items() if k in team_usernames}
    repo_prs = {k: v for k, v in team_prs.items()
                if v.get('base', {}).get('repo', {}).get('name', '') == repo}

    print(f'{"username":30s} {"state":10s} {"pull request"}')
    print(f'{"--------":30s} {"-----":10s} {"------------"}')
    for u, p in repo_prs.items():
        html_url = p.get('html_url', '')
        state = p.get('state', '[unknown]')
        print(f'{u:30s} {state:10s} {html_url}')
    tardies = [m for m in team_usernames if m not in repo_prs]
    for t in tardies:
        print(f'{t:30s} MISSING')

    n_prs = len(repo_prs)
    n_fail = len(tardies)
    print('\nSummary:')
    print(f'{n_prs:2d} pull requests OK')
    print(f'{n_fail:2d} pull requests MISSING')
    if n_fail == 0:
        print(f'The members of {team} made their homework!')
    else:
        print(f'The members of {team} have unfinished business!')


def to_cet_datetime(gitea_date_str, fmt='%Y-%m-%d %H:%M'):
    utc_dt = datetime.strptime(gitea_date_str, '%Y-%m-%dT%H:%M:%SZ')
    cet_dt = utc_dt.replace(tzinfo=timezone.utc)
    return cet_dt.astimezone(cet).strftime(fmt)


def fetch_team_usernames(ctx, owner, team):
    org_teams = http_get(ctx, f'orgs/{owner}/teams').json()
    teams = list(filter(lambda t: t.get('name', '') == team, org_teams))
    if len(teams) != 1:
        print(f'looked for team {team}, found', len(teams))
    team_id = teams[0].get('id', 0)
    team_members = http_get(ctx, f'teams/{team_id}/members').json()
    return [m.get('username', '') for m in team_members]


def add_user_to_team(ctx, login, team_id):
    res = http_put(ctx, f'teams/{team_id}/members/{login}')
    if res.status_code != 204:
        status = res.status_code
        print(f'add user "{login}" to team "{team_id}" failed: {status}')
    else:
        print(f'added user "{login}" to team "{team_id}"')


def register_user(ctx, username, fullname, email, notify):
    new_user = {
        'username': username,
        'email': email,
        'full_name': fullname,
        'must_change_password': True,
        'restricted': True,
        'send_notify': notify,
        'visibility': 'limited',
        'password': generate_password(),
    }
    res = http_post(ctx, 'admin/users', new_user)
    if res.status_code != 201:
        print(f'register user "{username}" failed: {res.status_code}')
    else:
        print(f'registered user "{username}"', res.json())


@cli.command(help='Generate a random password of given length')
@click.option('--length', default=24)
def genpw(length):
    print(generate_password(length))


def generate_password(length=24):
    alphabet = list(string.ascii_letters) + list(string.digits)
    password = ''
    for i in range(length):
        password += secrets.choice(alphabet)
    return password


def http_get(ctx, endpoint, params={}, accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Accept'] = accept
    return requests.get(url, headers=headers, params=params)


def http_post(ctx, endpoint, payload, content_type='application/json',
              accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Content-Type'] = content_type
    headers['Accept'] = accept
    return requests.post(url, json=payload, headers=headers)


def http_patch(ctx, endpoint, payload, content_type='application/json',
               accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Content-Type'] = content_type
    headers['Accept'] = accept
    return requests.patch(url, json=payload, headers=headers)


def http_put(ctx, endpoint, accept='application/json'):
    base_url = ctx.obj['BASE_URL']
    url = f'{base_url}/{endpoint}'
    headers = get_auth_header(ctx)
    headers['Accept'] = accept
    return requests.put(url, headers=headers)


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
