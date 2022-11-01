import re
import os
import click


def p_fail():
    """
    Print fail helper function.
    """
    click.echo(click.style('FAIL', fg='red'))


def p_pass():
    """
    Print pass helper function.
    """
    click.echo(click.style('PASS', fg='green'))


class GenericRule:
    """
    Semi-abstract class for single commit rule.

    It contains implementation for shared functionality 
    like printing and rule violation.
    """
    def __init__(self, rule_name, rule_text, rule_type):
        self.rule_name = rule_name
        self.rule_text = rule_text
        self.rule_type = rule_type

    # Implement checking of the rule against the commit
    def check(self, commit, config, broken_rules, output_format, file_tree):
        """
        Abstract method, implement in specific rules.
        """
        raise NotImplementedError('Abstract method. Should never be called.'
                                  ' Override for children.')

    # Print if rule passed or failed for 'rules' output format
    def print(self, violated, output_format):
        """
        Shared functionality for printing the rule.
        """
        if output_format == 'rules':
            print(f'  -> {self.rule_name}: ', end='')
            if violated:
                p_fail()
                print(f'     - {self.rule_text}')
            else:
                p_pass()

    def handle_rule_violated(self, broken_rules, violation_files):
        """
        Shared functionality to check how many times the rule was violated.
        """
        if self.violation_count == 0:
            broken_rules.append(self.rule_name)
        self.violation_count += 1
        violation_files.append(self.current_file)


class MessageRule(GenericRule):
    """
    Represents a Message rule (checks commit message).
    
    Message rule can be either plain, regex or wordlist.

    The application creates MessageRule like this:

    .. code::

        rule = MessageRule('relatively-forbidden', 'There are some relatively forbidden words in the message.', 'message', 'plain', 'abcd')
        commit =  {'message': 'This message surely contains abcdefg in it...'}
        broken_rules = []
        output_format = 'rules'
        rule.check(commit, 'not-needed-here', broken_rules, output_format, 'not-needed-here')
    """
    def __init__(self, rule_name, rule_text, rule_type, match_type,
                 match_pattern):
        super().__init__(rule_name, rule_text, rule_type)
        self.match_type = match_type
        self.match_pattern = match_pattern

    def handle_rule_violated(self, broken_rules, rule_violated, output_format):
        """
        Message rule needs custom check for rule violation count.
        """
        if rule_violated:
            broken_rules.append(self.rule_name)
        self.print(rule_violated, output_format)

    # Check for commit message violation + print it out
    def check(self, commit, config, broken_rules, output_format, file_tree):
        """
        Checks if the commit message violated the current rule.
        """
        try:
            message = commit['commit']['message'].lower()
        except KeyError:
            message = commit['message'].lower()
        if self.match_type == 'plain':
            rule_violated = self.match_pattern.lower() in message
            self.handle_rule_violated(broken_rules, rule_violated,
                                      output_format)
        elif self.match_type == 'regex':
            pattern = re.compile(self.match_pattern, re.IGNORECASE)
            rule_violated = pattern.search(message)
            self.handle_rule_violated(broken_rules, rule_violated,
                                      output_format)
        elif self.match_type == 'wordlist':
            file_path = self.match_pattern
            if not os.path.isabs(file_path):
                file_path = os.path.join(config[:config.rfind(os.path.sep)],
                                         file_path)
            with open(file_path) as f:
                for line in f.readlines():
                    rule_violated = line[:line.rfind(os.linesep)].lower() \
                                    in message
                    if rule_violated:
                        broken_rules.append(self.rule_name)
                        break
                self.print(rule_violated, output_format)


class PathRule(GenericRule):
    """
    Represents a Path rule (checks commit path).
    
    Path rule can be either plain, regex or wordlist.

    The application creates PathRule like this:
    
    .. code::

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
    """
    def __init__(self, rule_name, rule_text, rule_type, match_type,
                 match_pattern, rule_status):
        super().__init__(rule_name, rule_text, rule_type)
        self.match_type = match_type
        self.match_pattern = match_pattern
        self.rule_status = rule_status
        self.current_file = ''
        self.violation_count = 0

    def pcheck(self, config, broken_rules, output_format, message,
               violation_files):
        """
        Helper function to check if single item violated the rule.
        """
        if self.match_type == 'plain':
            rule_violated = self.match_pattern.lower() in message
            if rule_violated:
                self.handle_rule_violated(broken_rules, violation_files)
        elif self.match_type == 'regex':
            pattern = re.compile(self.match_pattern, re.IGNORECASE)
            match = pattern.search(message)
            if match:
                self.handle_rule_violated(broken_rules, violation_files)
        elif self.match_type == 'wordlist':
            file_path = self.match_pattern
            if not os.path.isabs(file_path):
                file_path = os.path.join(config[:config.rfind(os.path.sep)],
                                         file_path)
            with open(file_path) as f:
                for line in f.readlines():
                    rule_violated = line[:line.rfind(os.linesep)].lower() \
                                    in message
                    if rule_violated:
                        self.handle_rule_violated(broken_rules,
                                                  violation_files)
                        break

    def check(self, commit, config, broken_rules, output_format, file_tree):
        """
        Checks for all violations against this rule and prints them out.
        """
        violation_files = []
        self.violation_count = 0
        for entry in file_tree['files']:
            file_state = entry['status']
            if self.rule_status == '*' or self.rule_status == file_state:
                self.current_file = entry['filename']
                message = entry['filename'].lower()
                self.pcheck(config, broken_rules, output_format, message,
                            violation_files)
        if output_format == 'rules':
            print(f'  -> {self.rule_name}: ', end='')
            if self.violation_count > 0:
                p_fail()
                for wrong_file in violation_files:
                    print(f'     - {wrong_file}: {self.rule_text}')
            else:
                p_pass()


class StatsRule(GenericRule):
    """
    Represents a Stats rule.
    
    Stats rule can check commit or file statistics.

    The application creates StatsRule like this:
    
    .. code::

        rule = StatsRule('many-changes', 'Too little changes in the commit.', 'stats', 'changes', 'commit', 0, 2)
        file_tree =  {'stats': {'changes' : '10'}}
        broken_rules = []
        output_format = 'rules'
        rule.check('not-needed-here', 'not-needed-here', broken_rules, output_format, file_tree)
    """
    def __init__(self, rule_name, rule_text, rule_type, rule_stat, rule_scope,
                 rule_min, rule_max):
        super().__init__(rule_name, rule_text, rule_type)
        self.rule_stat = rule_stat
        self.rule_scope = rule_scope
        self.rule_min = int(rule_min)
        self.rule_max = int(rule_max)
        self.current_file = ''
        self.violation_count = 0

    def check_commit(self, commit, config, broken_rules, output_format,
                     file_tree):
        """
        Helper method to check if commit has correct stats.
        """
        check_value = int(file_tree['stats'][self.rule_stat])
        rule_violated = ((check_value > self.rule_max and self.rule_max != -1)
                         or check_value < self.rule_min)
        if rule_violated:
            broken_rules.append(self.rule_name)
        self.print(rule_violated, output_format)

    def check_file(self, commit, config, broken_rules, output_format,
                   file_tree, violation_files):
        """
        Helper method to check if file has correct stats.
        """
        for entry in file_tree['files']:
            check_value = entry[self.rule_stat]
            self.current_file = entry['filename']
            rule_violated = ((check_value > self.rule_max and
                             self.rule_max != -1)
                             or check_value < self.rule_min)
            if rule_violated:
                self.handle_rule_violated(broken_rules, violation_files)

    def check(self, commit, config, broken_rules, output_format, file_tree):
        """
        Checks if file or commit has correct stats by calling the helper methods
        and prints the result.
        """
        self.violation_count = 0
        violation_files = []
        if self.rule_scope == 'commit':
            self.check_commit(commit, config, broken_rules, output_format,
                              file_tree)
        elif self.rule_scope == 'file':
            self.check_file(commit, config, broken_rules, output_format,
                            file_tree, violation_files)
            if output_format == 'rules':
                print(f'  -> {self.rule_name}: ', end='')
                if self.violation_count > 0:
                    p_fail()
                    for wrong_file in violation_files:
                        print(f'     - {wrong_file}: {self.rule_text}')
                else:
                    p_pass()
