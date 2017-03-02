import logging
import os

from flask import render_template, redirect, url_for, request, abort
from flask import Blueprint
from flask_user import current_user

from WarnoConfig.models import db
from WarnoConfig.models import User


users = Blueprint('users', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)


@users.route('/users')
def list_users():
    """List WARNO Users.

    Returns
    -------
    users_template.html: HTML document
        Returns an HTML document with an argument for the list of users and their information.
    """
    if current_user.is_anonymous or current_user.authorizations != "engineer":
        abort(404)

    db_users = db.session.query(User).all()
    users_dict = [dict(name=user.name, email=user.email, location=user.location, position=user.position, id=user.id, username=user.username, active=user.is_active, password=user.password)
                  for user in db_users]

    return render_template('users_template.html', users=users_dict)



@users.route('/users/new', methods=['GET', 'POST'])
def new_user():
    """Add a new User to WARNO.

    Returns
    -------
    new_user.html: html document
        If the request method is 'GET', returns a form to create a new user.

    list_instruments: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_users function, redirecting the user to the list of users.
    """
    if current_user.is_anonymous or current_user.authorizations != "engineer":
        abort(404)

    if request.method == 'POST':
        # Get the information for the insert from the submitted form arguments
        # Lengths validated in views
        # TODO Email may need validation
        new_db_user = User()
        new_db_user.name = request.form.get('name')
        new_db_user.email = request.form.get('email')
        new_db_user.location = request.form.get('location')
        new_db_user.position = request.form.get('position')
        new_db_user.password = request.form.get('password')

        # New users only have the most basic authorization type, 'user'
        new_db_user.authorizations = "user"

        # Insert the new user into the database
        db.session.add(new_db_user)
        db.session.commit()

        # Redirect to the updated list of users
        return redirect(url_for("users.list_users"))

    # If the request is for the new form
    if request.method == 'GET':
        # Render the new user template
        return render_template('new_user.html')


@users.route('/users/<user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Update WARNO user.

    Parameters
    ----------
    user_id: integer
        Database user id of the user entry being updated.

    Returns
    -------
    new_user.html: HTML document
        If the request method is 'GET', returns a form to update user .

    list_users: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_users function, redirecting the user to the list of users.
    """
    if current_user.is_anonymous or current_user.authorizations != "engineer":
        abort(404)

    # If the form information has been received, update the user in the database
    if request.method == 'POST':
        # Get the user information from the request
        updated_user = db.session.query(User).filter(User.id == user_id).first()
        updated_user.username = request.form.get('username')
        updated_user.name = request.form.get('name')
        updated_user.email = request.form.get('email')
        updated_user.location = request.form.get('location')
        updated_user.position = request.form.get('position')
        updated_user.authorizations = request.form.get('authorizations')

        # Update user in the database
        db.session.commit()

        # Redirect to the updated list of users
        return redirect(url_for("users.list_users"))

    # If the request is to get the form, get the user and pass it to fill default values.
    if request.method == 'GET':
        db_user = db.session.query(User).filter(User.id == user_id).first()
        user = dict(username=db_user.username, name=db_user.name, email=db_user.email, location=db_user.location,
                    position=db_user.position, authorizations=db_user.authorizations)

        return render_template('edit_user.html', user=user)
