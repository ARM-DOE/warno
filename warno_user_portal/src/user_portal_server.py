from UserPortal import app
from WarnoConfig import config


if __name__ == '__main__':
    cfg = config.get_config_context()
    app.run(debug=True, host='0.0.0.0', port=cfg['setup']['user_portal_port'])

