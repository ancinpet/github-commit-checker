*********************
Github Commit Checker
*********************

Committee is a script that allows you to check commits on Github from CLI and web interface.

Features
========

- Check commit messages for words, regex patterns and wordlists
- Check commit statistics
- Check commit paths

Install
=======

To install the project, download the package:

.. code-block:: python

    python -m pip install --extra-index-url https://test.pypi.org/pypi committee-ancinpet

Documentation
=============

To check out the sources and documentation, download the source from:

a) `Github <https://github.com/ancinpet/github-commit-checker/>`_

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
