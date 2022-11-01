import click
import configparser
import os
import hmac
import hashlib

from flask import Flask, render_template, request
from committee.web.web_helper import internal_error, get_main
from committee.parsers.rule_parser import resolve_config
from committee.common_errors import err_config_load
from committee.git_comm import start_session


# Loads config (+ token and committee context)
# Checks reposlug validity
# Parses config (rules into rule set)
# Sorts rules according to their names
# Starts validation session
def run_app(config, author, path, ref, force, output_format,
            dry_run, reposlug, from_request=''):
    """
    Main entry point of the CLI application.

    It loads the config, parses it and checks reposlug validity.

    After, rules are created and sorted by name.

    Once all done, validation session is started.    
    """
    config_parser = configparser.ConfigParser(allow_no_value=True)
    with open(config) as f:
        try:
            config_parser.read_file(f)
        except configparser.MissingSectionHeaderError:
            err_config_load()
    try:
        git_token = config_parser.get('github', 'token')
        com_context = config_parser.get('committee', 'context')
    except configparser.NoOptionError:
        err_config_load()
    except configparser.NoSectionError:
        err_config_load()
    try:
        owner, repo = reposlug.split('/')
    except ValueError:
        raise click.BadParameter(f'Reposlug "{reposlug}" is not valid!',
                                 param_hint='\'REPOSLUG\'')
    rule_set = []
    resolve_config(config_parser, config, rule_set)
    rule_set.sort(key=lambda rule: rule.rule_name)
    start_session(git_token, com_context, owner, repo, author, path, ref,
                  rule_set, config, force, output_format, dry_run,
                  from_request)


@click.command()
@click.version_option(version='1.0')
@click.option('-c', '--config', metavar='FILENAME', required=True,
              help='Committee configuration file.')
@click.option('-a', '--author', metavar='AUTHOR', help='GitHub login or'
              ' email address of author for checking commits.')
@click.option('-p', '--path', metavar='PATH', help='Only commits containing'
              ' this file path will be checked.')
@click.option('-r', '--ref', metavar='REF', help='SHA or branch to check'
              ' commits from (default is the default branch).')
@click.option('-f', '--force', is_flag=True, help='Check even if commit has'
              ' already status with the same context.')
@click.option('-o', '--output-format', type=click.Choice(['none', 'commits',
              'rules']), default='commits', help='Verbosity level of the'
              ' output.', show_default=True)
@click.option('-d', '--dry-run', is_flag=True, help='No changes will be made'
              ' on GitHub.')
@click.argument('reposlug', nargs=1, required=True)
def main_app(config, author, path, ref, force, output_format,
             dry_run, reposlug):
    """
    CLI click wrapper for the application.

    Everything is forwarded into the main entry point.
    """
    run_app(config, author, path, ref, force, output_format, dry_run, reposlug)


def main():
    """
    Helper for package manager.
    """
    main_app(prog_name='committee')



def handle_ping():
    """
    Helper for ping server response.
    """
    return '', 200


def handle_push(config_name):
    """
    Helper for web app to start commit checking.
    """
    run_app(os.path.join(os.getcwd(), config_name), '', '', '', False, 'none',
            False, 'fitancinpet/committee-web-test', request.json)
    return 'OK', 200


def request_not_trusted(payload, com_secret, sha):
    """
    Checks if Github webhook uses communication secret and if it can be trusted.
    """
    if com_secret == '':
        return False

    signature = hmac.new(str.encode(com_secret), digestmod=hashlib.sha1,
                         msg=payload).hexdigest()
    return 'sha1=' + signature != sha


def post_main(com_secret, config_name):
    """
    Handles server POST requests.
    """
    if request_not_trusted(request.data, com_secret,
                           request.headers.get('X-Hub-Signature')):
        return 'Signature mismatch', 400

    if 'ping' in request.headers.get('X-Github-Event'):
        return handle_ping()
    elif 'push' in request.headers.get('X-Github-Event'):
        return handle_push(config_name)
    return 'Accepted but nothing was done.', 202


def create_app(config=None):
    """    
    Flash wrapper for the application.

    Everything is forwarded into the main entry point in case of webhook, 
    website is shown in case of GET request.
    """
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        config_name = os.environ.get('COMMITTEE_CONFIG')
        config_parser = configparser.ConfigParser(allow_no_value=True)
        try:
            with open(config_name) as cfg:
                try:
                    config_parser.read_file(cfg)
                except configparser.MissingSectionHeaderError:
                    return internal_error('Unable to load configuration.')
                config = config_parser._sections
                try:
                    git_token = config_parser.get('github', 'token')
                    com_secret = config_parser.get('github', 'secret',
                                                   fallback='')
                except configparser.NoOptionError:
                    return internal_error('Unable to load configuration.')
                except configparser.NoSectionError:
                    return internal_error('Unable to load configuration.')
                config.pop('github')
                if request.method == 'POST':
                    return post_main(com_secret, config_name)
                else:
                    return get_main(config, git_token)
        except TypeError:
            return internal_error('Unable to load configuration.')
        return 'Nothing to see here.', 204

    @app.route('/wordlists/<name>/')
    def wordlists(name):
        try:
            with open(f'../wordlists/{name}') as f:
                return render_template('wordlists.html', lines=f.readlines())
        except IOError:
            return internal_error('Word list does not exist.')

    return app
