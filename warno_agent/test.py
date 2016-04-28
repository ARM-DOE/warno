from flask import Flask
import wsgiref.simple_server
from time import sleep
import threading
import sys

app = Flask(__name__)
remote_server = wsgiref.simple_server.make_server('localhost', 10000, app)
remote_server.timeout = 0

test=1

global mydict 

mydict = {'test': 1}

@app.route('/')
def hello_world():
    update_value(mydict['test'])
    return "Hello World"+  str(mydict)

def update_value(i):
    mydict['test'] = i+1


def process_remote_requests():
        remote_server.handle_request()

if __name__ == '__main__':
    thread = threading.Thread(target = remote_server.serve_forever)
    thread.setdaemon = True
    try:
        thread.start()
        while True:
            if i % 1000000 == 0:
                print("Hello World"+ str(mydict['test']))

    except KeyboardInterrupt:
        remote_server.shutdown()
        sys.exit(0)



