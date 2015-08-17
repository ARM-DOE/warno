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
    cur = g.db.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    columns = [row[0] for row in rows]
    return render_template('dygraph.html', columns= columns)


#Generate a graph using a given key
@app.route('/generate_graph', methods=['GET', 'POST'])
def generate_graph():
    cur = g.db.cursor()

    key = request.args.get("key")
    print key;

    cur.execute('SELECT time, {k} FROM prosensing_paf'.format(k=key))
    rows = cur.fetchall()
    print rows[0]
    #? is iso format timezone ambiguous?
    x = [row[0].isoformat() for row in rows]
    y = [row[1] for row in rows]
    message = {"x": x,"y": y}
    message = json.dumps(message)
    
    return message


@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    #Add a new user to Warno
    cur = g.db.cursor()
    if request.method == 'POST':
        #Lengths validated in views
        #?email may need validation
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        position = request.form.get('position')
        password = request.form.get('password')

        cur.execute('''INSERT INTO users(name, "e-mail", location, position, password, authorizations) 
                    VALUES (%s, %s, %s, %s, %s, %s)''', (name, email, location, position, password, "None"))
        cur.execute('COMMIT')

        return redirect(url_for("list_users"))

    if request.method == 'GET':   
        return render_template('new_user.html')


@app.route('/users')
def list_users():
    cur = g.db.cursor()

    #?Dangerous query?
    # Create the list of users for the html table
    cur.execute('SELECT user_id, name, "e-mail", location, position FROM users')
    users = [dict(name=row[1], email=row[2], location=row[3], position=row[4], id=row[0]) for row in cur.fetchall()]

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
    cur = g.db.cursor()
    if request.method == 'POST':
        #Field lengths limited in the views
        abbv = request.form.get('abbv')
        name = request.form.get('name')
        itype = request.form.get('itype')
        vendor = request.form.get('vendor')
        description = request.form.get('description')
        frequency_band = request.form.get('frequency_band')
        site = request.form.get('site')

        cur.execute('''INSERT INTO instruments(name_short, name_long, type, vendor, description, frequency_band, site_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, itype, vendor, description, frequency_band, site))
        cur.execute('COMMIT')

        return redirect(url_for("list_instruments"))

    if request.method == 'GET':   
        # Create a set of sites and their ids for the dropdown in the add user form
        cur.execute('''SELECT site_id, name_short FROM sites ''')
        sites = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]
        return render_template('new_instrument.html', sites=sites)

@app.route('/instruments')
def list_instruments():
    #List Instruments
    cur = g.db.cursor()

    #?Dangerous query?
    # Create the list of users for the html table
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type, 
                i.vendor, i.description, i.frequency_band, s.name_short FROM instruments i 
                JOIN sites s ON (i.site_id = s.site_id)''')
    instruments = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5], 
                    frequency_band=row[6], location=row[7], id=row[0]) for row in cur.fetchall()]

    return render_template('instrument_list.html', instruments=instruments)

@app.route('/instruments/<instrument_id>')
def show_instrument(instrument_id):

    cur = g.db.cursor()
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type, 
            i.vendor, i.description, i.frequency_band, s.name_short, s.latitude, s.longitude 
            FROM instruments i JOIN sites s ON (i.site_id = s.site_id)
            WHERE i.instrument_id = %s''', (instrument_id,))
    row = cur.fetchone()
    instrument = dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5], 
                    frequency_band=row[6], location=row[7], latitude=row[8], longitude=row[9], id=row[0])

    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id WHERE l.instrument_id = %s 
                    ORDER BY time DESC LIMIT 5''', (instrument_id,))
    recent_logs = [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                        author=row[4]) for row in cur.fetchall()]
    if recent_logs:
        status = status_code_to_text(recent_logs[0]["status"])
    else:
        status = "OPERATIONAL"

    cur = g.db.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    columns = [row[0] for row in rows]

    return render_template('show_instrument.html', instrument=instrument, 
                            recent_logs=recent_logs, status= status, columns= columns)



#? May need to move this helper function, pulled from Stack Overflow
#Checks if the string is a valid decimal/floating point number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

@app.route('/sites/new', methods=['GET', 'POST'])
def new_site():
    #Add a new site to Warno

    if request.method == 'POST':
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

        #Uses helper function to check if it is a valid number
        if is_number(lat) and is_number(lon):
            cur = g.db.cursor()
            cur.execute('''INSERT INTO sites(name_short, name_long, latitude, longitude, facility, mobile, location_name) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, lat, lon, facility, mobile, location_name))
            cur.execute('COMMIT')

            return redirect(url_for("list_sites"))
        else:
            return redirect(url_for("new_site", error="Fields formatted incorrectly"))

    if request.method == 'GET':
        error = request.args.get('error')   
        return render_template('new_site.html', error= error)

@app.route('/sites')
def list_sites():
    cur = g.db.cursor()
    sql_query = '''SELECT s.name_short, s.name_long, s.latitude, s.longitude, 
                    s.facility, s.mobile, s.location_name, s.site_id FROM sites s'''
    cur.execute(sql_query)
    sites = [dict(abbv=row[0], name=row[1], latitude=row[2], longitude = row[3], facility=row[4], 
             mobile=row[5], location_name=row[6],id=row[7]) for row in cur.fetchall()]
    return render_template('site_list.html', sites=sites)

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
def submit_log_page():
    cur = g.db.cursor()
    instrument_sql = "select i.instrument_id, i.name_short, s.name_short from instruments i, sites s WHERE i.site_id = s.site_id"
    user_sql = "select u.user_id, u.name from users u"

    cur.execute(instrument_sql)
    instruments = [dict(id=row[0], name=row[2]+":"+row[1] ) for row in cur.fetchall()]

    cur.execute(user_sql)
    users = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

    return render_template('submit_log.html', users=users, instruments=instruments)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)
