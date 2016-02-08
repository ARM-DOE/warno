import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound

from WarnoConfig import config

users = Blueprint('users', __name__, template_folder='templates')


@users.route('/users')
def list_users():
    """List WARNO Users.

    Returns
    -------
    users_template.html: HTML document
        Returns an HTML document with an argument for the list of users and their information.
    """

    cur = g.db.cursor()
    cur.execute('SELECT user_id, name, "e-mail", location, position FROM users')
    users = [dict(name=row[1], email=row[2], location=row[3], position=row[4], id=row[0]) for row in cur.fetchall()]

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

    cur = g.db.cursor()

    if request.method == 'POST':
        # Get the information for the insert from the submitted form arguments
        # Lengths validated in views
        # TODO Email may need validation
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        position = request.form.get('position')
        password = request.form.get('password')

        # Insert the new user into the database
        cur.execute('''INSERT INTO users(name, "e-mail", location, position, password, authorizations)
                    VALUES (%s, %s, %s, %s, %s, %s)''', (name, email, location, position, password, "None"))
        cur.execute('COMMIT')

        # Redirect to the updated list of users
        return redirect(url_for("users.list_users"))

    # If the request is for the new form
    if request.method == 'GET':
        # Render the new user template
        return render_template('new_user.html')
