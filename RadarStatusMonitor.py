from flask import Flask, g, render_template
import psycopg2

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


@app.route('/users')
def show_users():
    cur = g.db.cursor()
    cur.execute('SELECT * FROM users')
    users = [dict(name=row[1], email=row[2], location=row[3], id=row[0]) for row in cur.fetchall()]
    return render_template('users_template.html', users=users)


def status_code_to_text(status):
    return status_text[int(status)]


status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}


@app.route('/sites')
def show_sites():
    cur = g.db.cursor()
    sql_query = 'SELECT s.name_short, s.name_long, s.latitude, s.longitude, s.site_id FROM sites s'
    cur.execute(sql_query)
    sites = [dict(abbv=row[0], name=row[1], latitude=row[2], longitude = row[3], id=row[4]) for row in cur.fetchall()]
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
    app.run(debug=True, host='0.0.0.0')
