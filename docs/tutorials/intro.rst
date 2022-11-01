*****************
What is Committee
*****************

Committee is a script that allows you to check commits on Github from CLI and web interface.

Features
========

- Check commit messages for words, regex patterns and wordlists
- Check commit statistics
- Check commit paths

.. _Example Config:

Example configuration
=====================
.. code-block:: cfg

    [github]
    token=<put your git token here>
    secret=<put github communication secret here>
    
    [committee]
    context=committee/fitancinpet
    
    [rule:no-shits]
    text=There is something shitty.
    type=path
    match=plain:SHIT
    
    [rule:persist-readme]
    text=README is important, do not delete it.
    type=path
    match=regex:^(README|README\.txt|README\.md|README\.rst)$
    status=removed
    
    [rule:relatively-forbidden]
    text=There are some relatively forbidden words in the message.
    type=message
    match=wordlist:../wordlists/forbidden.txt
    
    [rule:many-changes]
    text=Too many changes in the file.
    type=stats
    scope=file
    stat=changes
    max=500
