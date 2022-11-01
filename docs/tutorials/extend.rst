**********************
Inside the application
**********************

Project structure
=================

- exampleconfig.cfg (example committee configuration)
- setup.py (package setup and information)
- LICENSE (project licensing)
- README.rst (short project description)
- committee (project sources)
    - committee.py (main application entry point, flask + CLI)
    - git_comm.py (communication with Github API)
    - parsers (parsing of rules into rule classes)
    - rules (rule classes and checks implementation)
    - templates (html templates for the flask app)
    - web (Github authorization + index page rendering)
- docs (project documentation)
    - index.rst (main page)
    - tutorials (other pages)

How the project works
=====================

Basic printing
--------------

print_level function is used to distinguish the printing scope.

.. testsetup::

    from git_comm import print_level

Printing with verbosity set to commits:

.. testcode::

    print_level('This is a commit message', 'commits')

.. testoutput::

    This is a commit message

Printing with verbosity set to rules:

.. testcode::

    print_level('This is a rules message', 'rules')

.. testoutput::

    This is a rules message

All printing options:

.. testcode::

    print_level('This is a commit message', 'commits')
    print_level('This is a rules message', 'rules')
    print_level('This should not show', 'none')

.. testoutput::

    This is a commit message
    This is a rules message

Printing commit results
-----------------------

print_commit is used to print the rules that were violated.

.. testsetup::

    from git_comm import print_commit

When no rules are broken:

.. testcode::

    broken_rules = [] # Normally set by the application rule set
    output_format = 'commits'
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      => SUCCESS - No rules are violated by this commit.

When one rule is broken:

.. testcode::

    broken_rules = ['relatively-forbidden'] # Normally set by the application rule set
    output_format = 'commits'
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      => FAILURE - The commit violates rules: relatively-forbidden.

When more rules are broken:

.. testcode::

    broken_rules = ['no-shits', 'persist-readme', 'many-changes'] # Normally set by the application rule set
    output_format = 'commits'
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      => FAILURE - The commit violates rules: no-shits, persist-readme, many-changes.

CLI error handling
------------------

err_config_load is used to notify the user when something is wrong with the provided parameters

.. testsetup::

    from common_errors import err_config_load
    import click

When something in the CLI app goes wrong:

.. testcode::

    try:
        err_config_load()
        print('We should never get past here since there was an error.')
    except click.exceptions.BadParameter:
        print('Exception handled.')

.. testoutput::

    Exception handled.


Working with rules
------------------

GenericRule provides interface for basic manipulation that all Rules need to implement.
By default, 3 rule types are supported (MessageRule, PathRule, StatsRule).

.. testsetup::

    from rules.rule_validators import MessageRule, PathRule, StatsRule


Working with MessageRule
------------------------

Output needs to be set to rules for it to be printed:

.. testcode::

    rule = MessageRule('relatively-forbidden', 'There are some relatively forbidden words in the message.', 'message', 'plain', 'abcd')
    commit =  {'message': 'This message surely contains abcdefg in it...'}
    broken_rules = []
    output_format = 'rules'
    rule.check(commit, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'commits'
    rule.check(commit, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'none'
    rule.check(commit, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'rules'
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      -> relatively-forbidden: FAIL
         - There are some relatively forbidden words in the message.
      => FAILURE - The commit violates rules: relatively-forbidden, relatively-forbidden, relatively-forbidden.

No MessageRules violated:

.. testcode::

    rule = MessageRule('relatively-forbidden', 'There are some relatively forbidden words in the message.', 'message', 'plain', 'abcd')
    commitx =  {'message': 'This message does not contain alphabet in it...'}
    broken_rules = []
    output_format = 'rules'
    rule.check(commitx, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'commits'
    rule.check(commitx, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'none'
    rule.check(commitx, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    output_format = 'rules'
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      -> relatively-forbidden: PASS
      => SUCCESS - No rules are violated by this commit.
      

Working with PathRule
---------------------

PathRule is same as MessageRule, except it checks paths:

.. testcode::

    rule = PathRule('persist-readme', 'README is important, do not delete it.', 'path', 'regex', '^(README|README\.txt|README\.md|README\.rst)$', 'removed')
    file_tree =  {'files': [
        {
        'status': 'removed',
        'filename': "README.md"
        },
        {
        'status': 'added',
        'filename': "README.rst"
        },
        {
        'status': 'removed',
        'filename': "README.txt"
        }
    ]}
    broken_rules = []
    output_format = 'rules'
    rule.check('not-needed-here', 'not-needed-here', broken_rules, output_format, file_tree)
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      -> persist-readme: FAIL
         - README.md: README is important, do not delete it.
         - README.txt: README is important, do not delete it.
      => FAILURE - The commit violates rules: persist-readme.


Working with StatsRule
----------------------

StatsRule checks for commit statistics:

.. testcode::

    rule = StatsRule('many-changes', 'Too little changes in the commit.', 'stats', 'changes', 'commit', 0, 2)
    file_tree =  {'stats': {'changes' : '10'}}
    broken_rules = []
    output_format = 'rules'
    rule.check('not-needed-here', 'not-needed-here', broken_rules, output_format, file_tree)
    file_tree =  {'stats': {'changes' : '1'}}
    rule.check('not-needed-here', 'not-needed-here', broken_rules, output_format, file_tree)
    print_commit('', broken_rules, output_format)

.. testoutput::
    :options: +NORMALIZE_WHITESPACE

      -> many-changes: FAIL
         - Too little changes in the commit.
      -> many-changes: PASS
      => FAILURE - The commit violates rules: many-changes.
