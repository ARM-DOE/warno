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
