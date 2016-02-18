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
    This loads the config.yml file to provide the configuration context, then it appends the secrets.yml configuration.
    """
    base_path = os.getenv("DATA_STORE_PATH")
    config_filename = base_path + "config.yml"
    secrets_filename = base_path + "secrets.yml"

    # First we load the standard config yaml file.
    cfg = load_yaml_config(config_filename)
    # And then append anything from the secrets yaml file.
    cfg.update(load_yaml_config(secrets_filename))

    return cfg
