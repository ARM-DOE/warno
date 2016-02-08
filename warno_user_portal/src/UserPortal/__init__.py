from flask import Flask

from UserPortal.users import users
from UserPortal.sites import sites

app = Flask(__name__)
import UserPortal.views

app.register_blueprint(users)
app.register_blueprint(sites)
