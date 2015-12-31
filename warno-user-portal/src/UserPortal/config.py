import yaml
import os


def load_yaml_config(config_filename):
    """Load the configuration Object from the config file

    Loads a configuration Object from the config file.

    Returns
    -------
    config: dict
        Configuration Dictionary of Key Value Pairs
    """

    with open(config_filename, 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config


def get_config_context():
    """Load Configuration Context Object.
    This loads the config.yml file to provide the configuration context, then it appends custom values.
    """

    # First we load the standard config yaml file.
    base_path = os.getenv("USER_PORTAL_PATH")
    config_filename = base_path + "config.yml"
    cfg = load_yaml_config(config_filename)

    # Next we add a few fields that are only here for testing.

    cfg['database']['DB_PASS'] = 'warno'

    return cfg
