import click
import requests
import sys
import json
from flask import request


def print_level(to_print, output_format):
    """
    Wrapper to print only when output format is set to commits+
    """
    if output_format == 'commits' or output_format == 'rules':
        click.echo(to_print)


def get_statuses(broken_rules, git_session, com_context, owner, repo, sha,
                 state, description, target_url):
    """
    Posts a request to Github API for commit status.
    """
    return git_session.post(
             f"https://api.github.com/repos/{owner}/{repo}/statuses/{sha}",
             data=json.dumps({'state': state,
                              'description': description,
                              'context': com_context,
                              'target_url': target_url}))


def set_status(commit, broken_rules, git_session, com_context, owner, repo,
               sha, output_format, dry_run):
    """
    Sets the commit status unless it is a DRY RUN.
    """
    try:
        sha = commit['sha']
        target_url = ''
    except KeyError:
        target_url = request.base_url
    if dry_run:
        dry_text = click.style('DRY-RUN', fg='yellow')
        print_level(f'  ~> Updating commit status: {dry_text}', output_format)
    else:
        if broken_rules:
            rules = ', '.join(broken_rules)
            description = f'The commit violates rules: {rules}.'
            req = get_statuses(broken_rules, git_session, com_context, owner,
                               repo, sha, 'failure', description, target_url)
        else:
            req = get_statuses(broken_rules, git_session, com_context, owner,
                               repo, sha, 'success', 'No rules are violated by'
                               ' this commit.', target_url)
        if req.status_code >= 400:
            error = click.style('ERROR', fg="magenta")
            print_level(f'  ~> Updating commit status: {error}', output_format)
        else:
            ok = click.style('OK', fg="green")
            print_level(f'  ~> Updating commit status: {ok}', output_format)


bold_arrow = click.style('=> ', bold=True)


def handle_status(commit, broken_rules, git_session, com_context, owner, repo,
                  sha, force, output_format, dry_run):
    """
    Manages if status should be updated or not. If force is true, 
    it will always override it.
    """
    if force:
        set_status(commit, broken_rules, git_session, com_context, owner, repo,
                   sha, output_format, dry_run)
    else:
        page_number = 0
        old_req = ''
        while True:
            page_number += 1
            params = {'per_page': 100, 'page': page_number}
            status = git_session.get(f'https://api.github.com/repos/{owner}/'
                                     f'{repo}/commits/{sha}/status',
                                     params=params)
            statuses = status.json()['statuses']
            if statuses == old_req:
                break
            old_req = statuses
            for st in statuses:
                if st['context'] == com_context:
                    skipped = click.style('SKIPPED', fg='yellow')
                    print_level(f'  {bold_arrow}{skipped} - This commit '
                                'already has status with the same context.',
                                output_format)
                    return False
        set_status(commit, broken_rules, git_session, com_context, owner, repo,
                   sha, output_format, dry_run)
    return True


def print_commit(commit, broken_rules, output_format):
    """
    Prints whether the commit is ok or not based on rules broken.
    """
    if broken_rules:
        failure = click.style('FAILURE', fg='red')
        rules = ', '.join(broken_rules)
        print_level(f'  {bold_arrow}{failure} - The commit violates rules:'
                    f' {rules}.', output_format)
    else:
        success = click.style('SUCCESS', fg='bright_green')
        print_level(f'  {bold_arrow}{success} - No rules are violated by this'
                    ' commit.', output_format)


def resolve_commit(commit, rule_set, config, git_session, com_context, owner,
                   repo, force, output_format, dry_run):
    """
    Each commit is checked against all rules and its status is written
    """
    broken_rules = []
    try:
        sha = commit['sha']
    except KeyError:
        sha = commit['id']
    try:
        message = commit['commit']['message']
    except KeyError:
        message = commit['message']
    file_tree = git_session.get(f'https://api.github.com/repos/{owner}/{repo}'
                                f'/commits/{sha}').json()
    print_level(f'- {sha}: {message}', output_format)
    for rule in rule_set:
        rule.check(commit, config, broken_rules, output_format, file_tree)
    if handle_status(commit, broken_rules, git_session, com_context, owner,
                     repo, sha, force, output_format, dry_run):
        print_commit(commit, broken_rules, output_format)


def pull_commits(git_session, com_context, owner, repo, author, path, ref,
                 rule_set, config, force, output_format, dry_run):
    """
    Retrieves all commits from given repository. Handles Github pagination.
    """
    page_amount = 0
    while True:
        page_amount += 1
        params = {'author': author, 'path': path, 'sha': ref,
                  'per_page': 100, 'page': page_amount}
        req = git_session.get("https://api.github.com/repos/"
                              f"{owner}/{repo}/commits", params=params)
        if not req.ok:
            print("Failed to retrieve commits from "
                  f"repository {owner}/{repo}.", file=sys.stderr)
            sys.exit(1)
        for commit in req.json():
            resolve_commit(commit, rule_set, config, git_session,
                           com_context, owner, repo, force,
                           output_format, dry_run)
        if req.text == '[]' or len(req.text) < 20:
            break


def parse_commits(git_session, com_context, owner, repo, rule_set, config,
                  force, output_format, dry_run, from_request):
    """
    Retrieves the commit array from the Github request.
    """
    resolve_commit(from_request['commits'][0], rule_set, config, git_session,
                   com_context, owner, repo, force,
                   output_format, dry_run)


def start_session(git_token, com_context, owner, repo, author, path, ref,
                  rule_set, config, force, output_format, dry_run,
                  from_request):
    """
    Creates a Github session with token auth, 
    retrieves all commits and loops them
    """
    with requests.Session() as git_session:
        auth = {'Authorization': f'token {git_token}'}
        git_session.headers.update(auth)
        if from_request == '':
            pull_commits(git_session, com_context, owner, repo, author, path,
                         ref, rule_set, config, force, output_format, dry_run)
        else:
            parse_commits(git_session, com_context, owner, repo, rule_set,
                          config, force, output_format, dry_run, from_request)
