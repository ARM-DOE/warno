from flask import Flask

from . import users
from . import sites
from . import instruments
from . import logs

app = Flask(__name__)
import UserPortal.views

app.register_blueprint(users.users)
app.register_blueprint(sites.sites)
app.register_blueprint(instruments.instruments)
app.register_blueprint(logs.logs)
