import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound

from WarnoConfig import config
from WarnoConfig import database
from WarnoConfig.models import User

users = Blueprint('users', __name__, template_folder='templates')


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
