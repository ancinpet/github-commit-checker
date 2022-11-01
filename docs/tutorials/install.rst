************************
How to install Committee
************************

Install
=======

1. Install the package using

.. code-block:: python

    python -m pip install --extra-index-url https://test.pypi.org/pypi committee-ancinpet

2. `Create a Github API token for the committee account <https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token>`_ with repo scope.
#. If you want to use the web version, `create a Github communication secret <https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets>`_ for the repository you want to review.
#. Create a configuration file for the committee. Example configuration can be found here: :ref:`Example Config`.
#. Put your token into it and also fill in the context and rules. If you want to use the web version, also fill in the communication secret.
    a) If you want to run the CLI application, run:

    .. code-block:: python

        committee --help # Shows how to use the CLI app
        committee -c <your config path goes here> REPOSLUG # Runs the committee app, see the --help for more options

    b) If you want to use the web version, set the path to config file using the COMMITTEE_CONFIG system variable and run flask app:

    .. code-block:: python

        export COMMITTEE_CONFIG=<your config path goes here>
        export FLASK_APP=committee.py
        flask run

Documentation
=============

To check out the sources and documentation, download the source from:

a) `Github <https://github.com/fitancinpet/committee>`_
b) `TestPyPi <https://test.pypi.org/project/committee-ancinpet/#files>`_

Extract the sources if needed and go into the committee folder (main project folder).
From there, to build documentations, just do:

.. code-block:: python

    cd docs
    make html

The HTML pages are in _build/html.

Check if the documentation is updated by running doctests:

.. code-block:: python

    cd docs
    make doctest
