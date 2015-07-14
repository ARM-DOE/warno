from flask import Flask
import psutil
import os
app = Flask(__name__)


@app.route('/')
def hello_world():
    ret_message = 'Hello World! Event Manager is operational. CPU Usage on Event Manager VM is: %g \n ' % psutil.cpu_percent()
    ret_message2 = '\n Site is: %s' % os.environ.get('SITE')
    return ret_message + ret_message2


if __name__ == '__main__':
    app.run(host ='0.0.0.0', port=80, debug=True)
