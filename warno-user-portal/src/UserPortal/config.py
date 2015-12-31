import yaml


def load_config():
    """Load the configuration Object from the config file

    Loads a configuration Object from the config file.

    Returns
    -------
    config: dict
        Configuration Dictionary of Key Value Pairs
    """
    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config


def get_config_context():
    """Load Configuration Context Object.
    This loads the config.yml file to provide the configuration context.
    """
    cfg = {}

    cfg['DB_HOST'] = '192.168.50.100'
    cfg['DB_NAME'] = 'warno'
    cfg['DB_USER'] = 'warno'
    cfg['DB_PASS'] = 'warno'

    return cfg
