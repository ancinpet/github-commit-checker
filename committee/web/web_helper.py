import requests

from flask import render_template


def internal_error(reason):
    """
    Handles internal server error. Called when something goes wrong.
    """
    return 'Internal Server Error: ' + reason, 500


def get_main(config, git_token):
    """
    Handles the index page of the website app.

    Auth with Github, grabs the user's login and renders the template.
    """
    with requests.Session() as git_session:
        auth = {'Authorization': f'token {git_token}'}
        git_session.headers.update(auth)
        req = git_session.get("https://api.github.com/user").json()
        username = req['login']
    return render_template('index.html',
                           config=config.items(), username=username)
