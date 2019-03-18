import socket, socketserver
import utils
import config
from collections import deque

PACKET_SIZE = int(config.getValue("Network", "Packet_Size", "4096"))


class Client:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.settimeout(int(config.getValue("Network", "Timeout", "300")) / 1000)
        self.sendQueue = deque()
        self.recvQueue = b'' #deque()
        self.mainThread = None
    def connect(self, addr, port):
        utils.checkParamTypes("network.Client.connect", [addr, port], [{str}, {int}])
        self.socket.connect((addr, port))
    def startMain(self):
        self.mainThread = utils.Thread(target=self.mainLoop)
        self.mainThread.start()
    def abort(self):
        self.mainThread.stop()
        self.socket.close()
    def _send(self, msg):
        utils.checkParamTypes("network.Client.send", [msg], [{bytes}])
        self.sendQueue.append(msg)
    def _popRecvQueue(self, length):
        buf = self.recvQueue[:length]
        self.recvQueue = self.recvQueue[length:]
        return buf
    def _recv(self, length):
        # TODO: Timeout?
        buf = b''
        while len(buf) < length:
            if len(self.recvQueue) > 0:
                buf += self._popRecvQueue(min(length - len(buf), len(self.recvQueue)))
        return buf
    def recievePacket(self):
        # TODO: parse packet; await packet completion; decypher packet
        EPID = int.from_bytes(self._recv(1), "big")
        EPSIZE = int.from_bytes(self._recv(2), "big")
        EPDATA = self._recv(ESIZE)
        return EPID, EPDATA
    def mainLoop(self):
        while not self.mainThread.stopped():
            # Recieve what you can
            # TODO: Except broken pipes
            while True:
                try:
                    #self.recvQueue.append(self.socket.recv(PACKET_SIZE))
                    self.recvQueue += self.socket.recv(PACKET_SIZE)
                except: #socket.timeout:
                    break
            # Send what you can
            while self.sendQueue:
                try:
                    self.socket.send(self.sendQueue.popleft())
                except:
                    break


class Server:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.settimeout(int(config.getValue("Network", "Timeout", "300")) / 1000)
        self.clients = dict()
        self.mainThread = None
    def listen(self, addr="", port=-1):
        utils.checkParamTypes("network.Server.listen", [addr, port], [{str}, {int}])
        if port == -1:
            port = int(config.getValue("Network", "DefaultPort", "8887"))
        self.socket.bind((addr, port))
        self.socket.listen(int(config.getValue("Network", "MaxConnections", "15")))
    def startMain(self):
        self.mainThread = utils.Thread(target=self.mainLoop)
        self.mainThread.start()
    def abort(self):
        self.mainThread.stop()
        self.socket.close()
    def wrapClientObject(self, cl):
        utils.checkParamTypes("network.Server.createClientThread", [addr, cl], [{str}, {socket.socket}])
        client = Client()
        client.socket = cl
        client.socket.settimeout(int(config.getValue("Network", "Timeout", "300")) / 1000)
        client.startMain()
        return client
    def mainLoop(self):
        while not self.mainThread.stopped():
            # TODO: Close dead ones
            try:
                cl, addr = self.socket.accept()
                if addr in self.clients:
                    utils.showWarning("network.Server.mainLoop", "Present client tries to connect again from the same ip ({})".format(addr))
                else:
                    self.clients[addr] = wrapClientObject(cl)
            except:
                pass