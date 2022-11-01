import configparser
import re
import os

from committee.rules.rule_validators import MessageRule, PathRule, StatsRule
from committee.common_errors import err_config_load


def check_validity(config, match_type, match_pattern):
    """
    Checks if the rule from config meets required criteria 
    (regex needs to be valid, wordlist needs to exist on disk).
    """
    if match_type == 'regex':
        try:
            re.compile(match_pattern)
        except re.error:
            err_config_load()
    if match_type == 'wordlist':
        file_path = match_pattern
        if not os.path.isabs(file_path):
            file_path = os.path.join(config[:config.rfind(os.path.sep)],
                                     file_path)
            if not os.path.isfile(file_path):
                err_config_load()


def get_match(rule_match):
    """
    Parses match type and match pattern from the config 
    string and returns them.
    """
    try:
        match_type, match_pattern = rule_match.split(':')
    except ValueError:
        err_config_load()
    except AttributeError:
        err_config_load()
    if match_type not in ['plain', 'regex', 'wordlist']:
        err_config_load()
    return match_type, match_pattern


def resolve_message(config_parser, config, rule_set, section, rule_name,
                    rule_text, rule_type):
    """
    Parses a single MESSAGE rule and adds it to rule set
    """
    rule_match = config_parser.get(section, 'match', fallback=err_config_load)
    match_type, match_pattern = get_match(rule_match)
    check_validity(config, match_type, match_pattern)
    rule_set.append(MessageRule(rule_name, rule_text, rule_type, match_type,
                    match_pattern))


def resolve_path(config_parser, config, rule_set, section, rule_name,
                 rule_text, rule_type):
    """
    Parses a single PATH rule and adds it to rule set
    """
    rule_match = config_parser.get(section, 'match', fallback=err_config_load)
    rule_status = config_parser.get(section, 'status', fallback='*')
    match_type, match_pattern = get_match(rule_match)
    if rule_status not in ['modified', 'added', 'removed', '*']:
        err_config_load()
    check_validity(config, match_type, match_pattern)
    rule_set.append(PathRule(rule_name, rule_text, rule_type, match_type,
                    match_pattern, rule_status))


def resolve_stats(config_parser, rule_set, section, rule_name, rule_text,
                  rule_type):
    """
    Parses a single STATS rule and adds it to rule set
    """
    rule_stat = config_parser.get(section, 'stat', fallback=err_config_load)
    rule_scope = config_parser.get(section, 'scope', fallback='commit')
    try:
        rule_min = config_parser.getint(section, 'min', fallback=-1)
        rule_max = config_parser.getint(section, 'max', fallback=-1)
    except ValueError:
        err_config_load()
    if rule_scope == 'commit':
        if rule_stat not in ['total', 'additions', 'deletions']:
            err_config_load()
    elif rule_scope == 'file':
        if rule_stat not in ['changes', 'additions', 'deletions']:
            err_config_load()
    else:
        err_config_load()
    if rule_min == -1 and rule_max == -1:
        err_config_load()
    elif rule_min == -1:
        rule_min = 0
    rule_set.append(StatsRule(rule_name, rule_text, rule_type, rule_stat,
                    rule_scope, rule_min, rule_max))


def resolve_config(config_parser, config, rule_set):
    """
    Parses config file's rules into a rule set
    """
    for section in config_parser.sections():
        try:
            rule, name = section.split(':')
        except ValueError:
            continue
        if rule != 'rule':
            continue
        try:
            rule_text = config_parser.get(section, 'text')
            rule_type = config_parser.get(section, 'type')
        except configparser.NoOptionError:
            err_config_load()
        if rule_type == "message":
            resolve_message(config_parser, config, rule_set, section, name,
                            rule_text, rule_type)
        elif rule_type == "path":
            resolve_path(config_parser, config, rule_set, section, name,
                         rule_text, rule_type)
        elif rule_type == "stats":
            resolve_stats(config_parser, rule_set, section, name, rule_text,
                          rule_type)
        else:
            err_config_load()
