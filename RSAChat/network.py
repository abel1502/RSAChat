import socket, socketserver
from . import utils
from . import config
from collections import deque
import time

PACKET_SIZE = int(config.getValue("Network", "Packet_Size", "4096"))


class Client:
    def __init__(self):
        self.socket = socket.socket()
        #self.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
        self.socket.setblocking(False)
        self.sendQueue = b''
        self.recvQueue = b''
        self.mainThread = None
    def connect(self, addr, port):
        utils.checkParamTypes("network.Client.connect", [addr, port], [{str}, {int}])
        try:
            self.socket.connect((addr, port))
        except Exception as e:
            if e.args[0] != 10035:
                raise e
            else:
                utils.showWarning("DEBUG", e)
    def startMain(self):
        self.mainThread = utils.Thread(target=self.mainLoop)
        self.mainThread.start()
    def abort(self):
        self.mainThread.stop()
        self.socket.close()
    def _send(self, msg):
        utils.checkParamTypes("network.Client.send", [msg], [{bytes}])
        self.sendQueue += msg
    def _popSendQueue(self, length):
        buf = self.sendQueue[:length]
        self.sendQueue = send.recvQueue[length:]
        return buf    
    def _popRecvQueue(self, length):
        buf = self.recvQueue[:length]
        self.recvQueue = self.recvQueue[length:]
        return buf
    def _recv(self, length):
        # TODO: Timeout?
        buf = b''
        sTime = time.process_time()
        while time.process_time() - sTime < 15 and len(buf) < length: # Port to config
            if len(self.recvQueue) > 0:
                buf += self._popRecvQueue(min(length - len(buf), len(self.recvQueue)))
        if len(buf) < length:
            self.recvQueue = buf + self.recvQueue
            utils.raiseException("network.Client._recv", "Not enough data to recieve")
        return buf
    def recievePacket(self):
        # TODO: parse packet; await packet completion; decypher packet; fix this shit)
        EPID = int.from_bytes(self._recv(1), "big")
        EPSIZE = int.from_bytes(self._recv(2), "big")
        EPDATA = self._recv(ESIZE)
        return EPID, EPDATA
    def mainLoop(self):
        while not self.mainThread.stopped:
            if len(self.sendQueue) > 0:
                try:
                    c.send(self._popSendQueue(128))
                except Exception as e:
                    if e.args[0] != 10035:
                        utils.ShowWarning("network.Client.mainLoop", e)
            time.sleep(0.5)
            try:
                self.recvQueue += c.recv(128)
            except Exception as e:
                if e.args[0] != 10035:
                    utils.ShowWarning("network.Client.mainLoop", e)

class Server:
    def __init__(self):
        self.socket = socket.socket()
        #self.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
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
        for addr in self.clients:
            self.clients[addr].abort()
        self.socket.close()
    def wrapClientObject(self, cl):
        utils.checkParamTypes("network.Server.createClientThread", [cl], [{socket.socket}])
        client = Client()
        client.socket = cl
        #client.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
        client.socket.setblocking(False)
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
                    self.clients[addr] = self.wrapClientObject(cl)
            except Exception as e:
                print(e)
                pass