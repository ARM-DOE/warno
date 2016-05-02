import logging
import os

from flask import Flask

from . import users
from . import sites
from . import instruments
from . import logs


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        server = environ.get('HTTP_X_FORWARDED_SERVER', '')
        if server:
            environ['HTTP_HOST'] = server
        return self.app(environ, start_response)


log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"
# Logs to the main log
logging.basicConfig( format='%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s',
                     filename='%scombined.log' % log_path,
                     filemode='a', level=logging.DEBUG)

# Logs to the user portal log
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
# Add user portal handler to the main werkzeug logger
logging.getLogger("werkzeug").addHandler(up_handler)


app = Flask(__name__)
import UserPortal.views

app.register_blueprint(users.users)
app.register_blueprint(sites.sites)
app.register_blueprint(instruments.instruments)
app.register_blueprint(logs.logs)

app.wsgi_app = ReverseProxied(app.wsgi_app)
