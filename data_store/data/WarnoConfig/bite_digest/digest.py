import socket
import ast

from select import select

class Digest():

    MESSAGE_END_DELIMITER = "EOS\xff"
    DEBUG = False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, debug=False):
        self.DEBUG = debug

    def get_data(self, address="198.124.104.50", port=3000):
        target_address = (address, port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(target_address)
        self.s.send("interrogate")

        message = self.recvall(self.s)

        if self.DEBUG:
            print(">>DEBUG>>>Message Received Repr:")
            print(repr(message))

        data_block = ""
        if len(message) > 4:
            if (message[-4:] == self.MESSAGE_END_DELIMITER):
                data_block = message[:-4]

        if self.DEBUG:
            print (">>DEBUG>>>Data Block before literal_eval")
            print data_block

        data = ast.literal_eval(data_block)

        if self.DEBUG:
            print (">>DEBUG>>>Eval'ed data type:")
            print type(data)
            print (">>DEBUG>>>Number of keys for data (assumes dict):")
            print len(data.keys())

        if isinstance(data, dict):
            for key in data.keys():
                if isinstance(data[key], dict):
                    data[key] = data[key]["value"]
        if self.DEBUG:
            print (">>DEBUG>>>Data after conversions of second layer dicts into flat values:")
            print data

        return data



    def recvall(self, sock):
        self.buffer = ""
        while sock in select([sock, ], [], [], 1)[0]:
            self.buffer += sock.recv(1000)
            if self.buffer is '':
                return self.buffer
        return self.buffer

if __name__ == "__main__":
    d = Digest()

    d.get_data()