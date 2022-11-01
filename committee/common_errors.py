import click


def err_config_load():
    """
    The most common error used in the application, called when 
    a parameter is wrong.
    """
    raise click.BadParameter('Failed to load the configuration!',
                             param_hint='\'-c\' / \'--config\'')
