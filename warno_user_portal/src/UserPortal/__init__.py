from flask import Flask

from UserPortal.users import users
from UserPortal.sites import sites
from UserPortal.instruments import instruments

app = Flask(__name__)
import UserPortal.views

app.register_blueprint(users)
app.register_blueprint(sites)
app.register_blueprint(instruments)
