import logging
import os

from flask import render_template, redirect, url_for, request
from flask import Blueprint

from WarnoConfig import config
from WarnoConfig import database
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

    db_users = database.db_session.query(User).all()
    users = [dict(name=user.name, email=user.email, location=user.location, position=user.position, id=user.id)
             for user in db_users]

    return render_template('users_template.html', users=users)


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

    if request.method == 'POST':
        # Get the information for the insert from the submitted form arguments
        # Lengths validated in views
        # TODO Email may need validation
        new_user = User()
        new_user.name = request.form.get('name')
        new_user.email = request.form.get('email')
        new_user.location = request.form.get('location')
        new_user.position = request.form.get('position')
        new_user.password = request.form.get('password')

        # Insert the new user into the database
        database.db_session.add(new_user)
        database.db_session.commit()

        # Redirect to the updated list of users
        return redirect(url_for("users.list_users"))

    # If the request is for the new form
    if request.method == 'GET':
        # Render the new user template
        return render_template('new_user.html')


@users.route('/users/<user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Update WARNO user.

    Returns
    -------
    new_user.html: HTML document
        If the request method is 'GET', returns a form to update user .

    list_users: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_users function, redirecting the user to the list of users.
    """
    # If the form information has been received, update the user in the database
    if request.method == 'POST':
        # Get the user information from the request
        updated_user = database.db_session.query(User).filter(User.id == user_id).first()
        updated_user.name = request.form.get('name')
        updated_user.email = request.form.get('email')
        updated_user.location = request.form.get('location')
        updated_user.position = request.form.get('position')
        updated_user.password = request.form.get('password')

        # Update user in the database
        database.db_session.commit()

        # Redirect to the updated list of users
        return redirect(url_for("users.list_users"))

    # If the request is to get the form, get the user and pass it to fill default values.
    if request.method == 'GET':
        db_user = database.db_session.query(User).filter(User.id == user_id).first()
        user = dict(name=db_user.name, email=db_user.email, location=db_user.location, position=db_user.position)

        return render_template('edit_user.html', user=user)
