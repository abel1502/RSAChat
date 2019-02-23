import socket, socketserver
import utils
import config
from collections import deque


class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.settimeout(config.getValue("Network", "Timeout"))
        self.sendQueue = deque()
        self.recvQueue = deque()
    def connect(self, addr, port):
        utils.checkParamTypes("network.Client.connect", [addr, port], [{str}, {int}])
        self.socket.connect((addr, port))
    def mainLoop(self):
        # TODO
        while True:
            self.recvQueue.append()


class Server:
    def __init__(self):
        pass