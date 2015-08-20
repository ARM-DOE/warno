from flask import Flask, g, render_template, \
                    request, redirect, url_for
import psycopg2
import json
import random #?Not necessary after debugging completes

DB_HOST = '192.168.50.100'
DB_NAME = 'warno'
DB_USER = 'warno'
DB_PASS = 'warno'

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (DB_HOST, DB_NAME, DB_USER, DB_PASS))


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/dygraph')
def show_dygraph():
    #Get information for the dygraph partial template

    #Initialize the database cursor
    cur = g.db.cursor()
    #Select the columns from the data table.
    #Allows the template to create a dropdown list with fixed values.
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    #Put all of  the names in one list
    columns = [row[0] for row in rows]

    #Render the template and pass the list of columns
    return render_template('dygraph.html', columns= columns)

@app.route('/generate_graph', methods=['GET', 'POST'])
def generate_graph():
    #Generate a graph using a given key
    #Initialize the database
    cur = g.db.cursor()

    #Get the key and instrument_id from the arguments passed to the function.
    #The key is plotted against time in the graph data to be returned.
    #The key is from a selection on the form, not free typed by the user.
    #The instrument_id indicates which instrument's data to use for the graph.
    key = request.args.get("key")
    instrument_id = request.args.get("instrument_id")

    #Selects the time and the "key" column from the data table for the supplied instrument_id
    #? May be dangerous to reference the key into the table like this?
    cur.execute('SELECT time, {k} FROM prosensing_paf WHERE instrument_id = {i}'.format(k= key, i= instrument_id))
    rows = cur.fetchall()

    #Converts the data into a JSON friendly format, involves time type conversion
    #? Is iso format timezone ambiguous?
    #? Considered both list comprehensions at once, but to achieve 2 lists did not seem viable.
    x = [row[0].isoformat() for row in rows]
    y = [row[1] for row in rows]
    #Format the message
    message = {"x": x,"y": y}
    #Convert to JSON
    message = json.dumps(message)
    
    #Send out the JSON message
    return message


@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    #Add a new user to Warno
    #Initialize the cursor for the database
    cur = g.db.cursor()

    if request.method == 'POST':
        #Get the information for the insert from the submitted form arguments
        #Lengths validated in views
        #?email may need validation
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        position = request.form.get('position')
        password = request.form.get('password')

        #Insert the new user into the database
        cur.execute('''INSERT INTO users(name, "e-mail", location, position, password, authorizations) 
                    VALUES (%s, %s, %s, %s, %s, %s)''', (name, email, location, position, password, "None"))
        cur.execute('COMMIT')

        #Redirect to the updated list of users
        return redirect(url_for("list_users"))

    #If the request is for the new form
    if request.method == 'GET':   
        #Render the new user template
        return render_template('new_user.html')


@app.route('/users')
def list_users():
    cur = g.db.cursor()

    #?Dangerous query?
    # Grab the list of users and their information
    cur.execute('SELECT user_id, name, "e-mail", location, position FROM users')
    # Add each user and their information to a dictionary in the list of users
    users = [dict(name=row[1], email=row[2], location=row[3], position=row[4], id=row[0]) for row in cur.fetchall()]

    #Render the template with the list of users
    return render_template('users_template.html', users=users)


def status_code_to_text(status):
    return status_text[int(status)]


status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}

@app.route('/instruments/new', methods=['GET', 'POST'])
def new_instrument():
    #Add a new instrument to Warno
    #Initialize the cursor for the database
    cur = g.db.cursor()

    #If the form information has been received, insert the new instrument into the table
    if request.method == 'POST':
        #Get the instrument information from the request
        #Field lengths limited in the views
        abbv = request.form.get('abbv')
        name = request.form.get('name')
        itype = request.form.get('itype')
        vendor = request.form.get('vendor')
        description = request.form.get('description')
        frequency_band = request.form.get('frequency_band')
        site = request.form.get('site')

        #Insert a new instrument into the database
        cur.execute('''INSERT INTO instruments(name_short, name_long, type, vendor, description, frequency_band, site_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, itype, vendor, description, frequency_band, site))
        cur.execute('COMMIT')

        #Redirect to the updated list of instruments
        return redirect(url_for("list_instruments"))

    #If the request is to get the form
    if request.method == 'GET':   
        # Get a list of sites and their ids for the dropdown in the add user form
        cur.execute('''SELECT site_id, name_short FROM sites ''')
        #Add each site as a dictionary to a list of sites
        sites = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

        #Return the list of sites to the new instrument form
        return render_template('new_instrument.html', sites=sites)

@app.route('/instruments')
def list_instruments():
    #List Instruments
    cur = g.db.cursor()

    #?Dangerous query?
    # Grab the list of instruments and their information
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type, 
                i.vendor, i.description, i.frequency_band, s.name_short, s.site_id FROM instruments i 
                JOIN sites s ON (i.site_id = s.site_id) ORDER BY i.instrument_id ASC''')
    #Create a list of dictionaries, with each dictionary being an instrument and its information
    instruments = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5], 
                    frequency_band=row[6], location=row[7], site_id= row[8], id=row[0]) 
                    for row in cur.fetchall()]

    #Render the template with the generated
    return render_template('instrument_list.html', instruments=instruments)

@app.route('/instruments/<instrument_id>')
def show_instrument(instrument_id):

    #Initialize the database cursor
    cur = g.db.cursor()

    #Grabs the instrument information for the instrument matching "instrument_id" from the database
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type, 
            i.vendor, i.description, i.frequency_band, s.name_short, s.latitude, s.longitude, s.site_id 
            FROM instruments i JOIN sites s ON (i.site_id = s.site_id)
            WHERE i.instrument_id = %s''', (instrument_id,))
    row = cur.fetchone()
    #Inserts the information from the query into a dictionary object
    instrument = dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5], 
                      frequency_band=row[6], location=row[7], latitude=row[8], longitude=row[9],
                      site_id=row[10], id=row[0])

    #Grabs the most recent 5 logs for the instrument matching "instrument_id" from the database
    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id WHERE l.instrument_id = %s 
                    ORDER BY time DESC LIMIT 5''', (instrument_id,))
    #Creates a list of dictionaries, each dictionary being one of the log entries
    recent_logs = [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                        author=row[4]) for row in cur.fetchall()]

    #If there are any log, the most recent log (the first of the list) has the status
    #Uses helper function to print the status code to text
    if recent_logs:
        status = status_code_to_text(recent_logs[0]["status"])
    #If there are no recent logs, assume the instrument is operational
    else:
        status = "OPERATIONAL"

    #Select the list of available columns in the prosensing_paf data table.
    #This is used in the template to select the key to plot against time in the
    #graph generation function
    cur = g.db.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    #Add each name to the list of columns
    columns = [row[0] for row in rows]

    #Render the template with the generated information
    return render_template('show_instrument.html', instrument=instrument, 
                            recent_logs=recent_logs, status= status, columns= columns)




def is_number(s):
    #? May need to move this helper function, pulled from Stack Overflow
    #Checks if the string is a valid decimal/floating point number
    try:
        #Attempts to convert the string into a float. Returns true if it works
        float(s)
        return True
    except ValueError:
        #If the conversion doesn't work, return false
        return False

@app.route('/sites/new', methods=['GET', 'POST'])
def new_site():
    #Add a new site to Warno

    #If the method is post, the user has submitted the information in the form.
    #Try to insert the new site into the database, if the values are incorrect redirect
    #with an appropriate error message
    if request.method == 'POST':
        #Get the parameters from the url request
        #Field lengths limited in the views
        abbv = request.form.get('abbv')
        name = request.form.get('name')
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        facility = request.form.get('facility')
        mobile = request.form.get('mobile')
        location_name = request.form.get('location_name')

        #If the "mobile" box was checked in new_site, mobile is True. Else, false
        if mobile == "on":
            mobile = True;
        else:
            mobile = False;

        #Uses helper function to check if latitude and longitude are valid numbers
        #If so, insert the information into the database
        #If not, redirect with an error message
        if is_number(lat) and is_number(lon):
            #Insert the information into the database
            cur = g.db.cursor()
            cur.execute('''INSERT INTO sites(name_short, name_long, latitude, longitude, facility, mobile, location_name) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, float(lat), float(lon), facility, mobile, location_name))
            cur.execute('COMMIT')

            #After insertion, redirect to the updated list of sites
            return redirect(url_for("list_sites"))
        else:
            #Return to the new site form with an error indicating Latitude and Longitude must be numbers
            return redirect(url_for("new_site", error="Latitude and Longitude must be numbers."))

    #If the browser requests the form, renders the form.  If there was an error from before,
    #adds the error into the render call
    if request.method == 'GET':
        #If there was an error from before, pulls and passes the error message
        #Otherwise, error will be an empty string and will not show up in the template
        error = request.args.get('error')   
        return render_template('new_site.html', error= error)

@app.route('/sites')
def list_sites():
    cur = g.db.cursor()
    #Grab the list of all ARM sites and their info from the database
    sql_query = '''SELECT s.name_short, s.name_long, s.latitude, s.longitude, 
                    s.facility, s.mobile, s.location_name, s.site_id FROM sites s'''
    cur.execute(sql_query)
    #Insert each site and its information as a dictionary into the list of sites
    sites = [dict(abbv=row[0], name=row[1], latitude=row[2], longitude = row[3], facility=row[4], 
             mobile=row[5], location_name=row[6],id=row[7]) for row in cur.fetchall()]

    #Render the sites list with the information
    return render_template('site_list.html', sites=sites)

@app.route('/sites/<site_id>')
def show_site(site_id):

    #Initialize the cursor
    cur = g.db.cursor()

    #Get the site information for the current site_id
    cur.execute('''SELECT site_id, name_short, name_long, latitude, longitude, facility, 
                    mobile, location_name FROM sites WHERE site_id = %s''', (site_id,))
    row = cur.fetchone()
    site = dict(abbv=row[1], name=row[2], latitude=row[3], longitude=row[4], 
                facility=row[5], mobile=row[6], location_name=row[7], id=row[0])

    #Get the 5 most recent logs to display
    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name, i.name_short
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id JOIN instruments i ON i.instrument_id = l.instrument_id 
                    JOIN sites s ON i.site_id = s.site_id
                    WHERE s.site_id = %s 
                    ORDER BY time DESC LIMIT 5''', (site_id,))
    recent_logs = [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                        author=row[4], instrument=row[5]) for row in cur.fetchall()]

    #Taken from "show-radar_status" and matched to current site_id
    #Get the most recent log for each instrument to determine its current status
    sql_query = '''SELECT i.instrument_id, users.name, l1.status
                FROM instruments i
                JOIN instrument_logs l1 ON (i.instrument_id = l1.instrument_id)
                LEFT OUTER JOIN instrument_logs l2 ON (i.instrument_id = l2.instrument_id AND
                    (l1.time < l2.time OR l1.time = l2.time AND l1.instrument_id < l2.instrument_id))
                LEFT OUTER JOIN sites
                      ON (sites.site_id = i.site_id)
                    LEFT OUTER JOIN users
                      ON (l1.author_id = users.user_id)
                WHERE (l2.instrument_id IS NULL AND i.site_id = %s)  ORDER BY sites.name_short;
            '''
    cur.execute(sql_query, (site_id,))
    #Put into dictionary to add status codes and the last log author to instrument list later
    status = {row[0]: dict(last_author=row[1], status_code=row[2]) for row in cur.fetchall()}

    #Get a list of instruments and the information for them.  Originally planned to combine this
    #query and the status query, however didn't seem to return instrument information if there were
    #no logs attached to the instrument
    #Assume the status is operational unless the status has changed, handled afterward
    cur.execute('''SELECT instrument_id, name_short, name_long, type, vendor, frequency_band, description
                    FROM instruments WHERE site_id = %s''', (site_id,))
    rows = cur.fetchall()
    instruments = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], frequency_band=row[5], 
                        description=row[6], status=1, last_author="", id=row[0]) for row in rows]

    #For each instrument, if there is a corresponding status entry from the query above,
    #add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['last_author'] = status[instrument['id']]["last_author"]
        instrument['status'] = status_code_to_text(instrument['status'])

    #Return the information and render the show_site template
    return render_template('show_site.html', site=site, instruments=instruments, recent_logs=recent_logs)

@app.route('/radar_status')
def show_radar_status():
    cur = g.db.cursor()
    sql_query = '''SELECT i.name_short, sites.name_short, l1.contents, users.name, l1.status
                FROM instruments i
                JOIN instrument_logs l1 ON (i.instrument_id = l1.instrument_id)
                LEFT OUTER JOIN instrument_logs l2 ON (i.instrument_id = l2.instrument_id AND
                    (l1.time < l2.time OR l1.time = l2.time AND l1.instrument_id < l2.instrument_id))
                LEFT OUTER JOIN sites
                      ON (sites.site_id = i.site_id)
                    LEFT OUTER JOIN users
                      ON (l1.author_id = users.user_id)
                WHERE l2.instrument_id IS NULL  ORDER BY sites.name_short;
            '''

    cur.execute(sql_query)
    logs = [dict(instrument_name=row[0], site=row[1],
                 contents=row[2], author=row[3], status=status_code_to_text(row[4])) for row in cur.fetchall()]
    return render_template('radar_status.html', logs=logs)

@app.route('/submit_log')
def new_log():
    #Submit a log for a Warno instrument
    #Differently formatted from the other new pages, designed to allow remote functions to
    #send get requests with parameters to make new log entries

    #Initialize the database cursor
    cur = g.db.cursor()
    #Set the default error message. Will not show on template when its the empty string
    error = ""
    #Get arguments from url if there were any specified
    user_id = request.args.get('user-id')
    instrument_id = request.args.get('instrument')
    time = request.args.get('time')
    status = request.args.get('status')
    contents = request.args.get('contents')

    #If there is valid data entered with the get request, insert and redirect to the instrument
    #that the log was placed for
    #(If a user visits the page for the first time with no arguments, skips this section and renders form.)
    if user_id and instrument_id and status and time:
        #Attempt to insert an item into the database. Try/Except is necessary because the timedate
        #datatype the database expects has to be formatted correctly.
        try:
            #Insert the new log into the database
            cur.execute('''INSERT INTO instrument_logs(time, instrument_id, author_id, contents, status) 
                           VALUES (%s, %s, %s, %s, %s)''', (time, instrument_id, user_id, contents, status))
            cur.execute('COMMIT')
            #Redirect to the instrument page that the log was submitted for.  Log will likely appear on page
            #May not appear if the date was set to older than the 5 most recent logs
            return redirect(url_for('show_instrument', instrument_id=instrument_id))
        except psycopg2.DataError:
            #If the timedate object expected by the database was incorrectly formatted, error is set
            #for when the page is rendered
            error = "Invalid Date/Time Format"
        #Commit required, especially if there is an exception, otherwise the cursor breaks on the next execute
        cur.execute('COMMIT')

    #If there was no valid insert, render form normally
    #Set the sql command strings
    instrument_sql = "select i.instrument_id, i.name_short, s.name_short from instruments i, sites s WHERE i.site_id = s.site_id"
    user_sql = "select u.user_id, u.name from users u"

    #Get a list of instruments to select from in the form
    cur.execute(instrument_sql)
    #Format the instrument names to be more descriptive and add dictionary for each entry to a list
    instruments = [dict(id=row[0], name=row[2]+":"+row[1] ) for row in cur.fetchall()]

    #Get a list of users to choose who submitted the log.
    #This list will be selected from in the form
    cur.execute(user_sql)
    #Add a dictionary for each site and its information to the list of sites
    users = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

    #Render the template with all of the information and the error(if there was one)
    return render_template('new_log.html', users=users, instruments=instruments, status=status_text, error=error)



@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)
