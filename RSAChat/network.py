import socket, socketserver
from . import utils
from . import config
from collections import deque
import time
import asyncio

PACKET_SIZE = int(config.getValue("Network", "Packet_Size", "4096"))
SERVER = None


def addClientToServer(cl):
    if SERVER is not None:
        SERVER.clients.append(cl)


def startServer(host="", port=8887):
    SERVER = Server(host, port)
    SERVER.start()


class Server:
    def __init__(self, host="", port=8887):
        self.eventLoop = asyncio.get_event_loop()
        coro = self.eventLoop.create_server(ServerClientProtocol, host, port)
        self.aioServer = self.eventLoop.run_until_complete(coro)
        self.mainThread = None
        self.clients = []  # Dict?....
    def start(self):
        self.mainThread = utils.startThread(self.eventLoop.run_forever)
    def abort(self):
        # TODO: Close clients
        self.aioServer.close()
        self.eventLoop.stop()
        self.eventLoop.close()


class ServerProtocol(asyncio.Protocol):
    def send(self, data):
        self.transport.write(data)
    def recv(self, length):
        buf = self.recvBuf[:length]
        self.recvBuf = self.recvBuf[length:]
        return buf
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        #print('Connection from {}'.format(peername))
        self.transport = transport
        addClientToServer(self)
        self.recvBuf = b''
    def data_received(self, data):
        self.recvBuf += data


def startClient(host, port=8887):
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(lambda: ClientProtocol(loop), host, port)
    client = loop.run_until_complete(coro)
    mainThread = utils.startThread(loop.run_forever)
    return loop, client, mainThread


class ClientProtocol(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop
    def send(self, data):
        self.transport.write(data)
    def recv(self, length):
        buf = self.recvBuf[:length]
        self.recvBuf = self.recvBuf[length:]
        return buf    
    def connection_made(self, transport):
        self.transport = transport
        self.recvBuf = b''
    def data_received(self, data):
        self.recvBuf += data
    def connection_lost(self, exc):
        self.loop.stop()


#class Client:
    #def __init__(self):
        #self.socket = socket.socket()
        ##self.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
        #self.sendQueue = b''
        #self.recvQueue = b''
        #self.mainThread = None
    #def connect(self, addr, port):
        #utils.checkParamTypes("network.Client.connect", [addr, port], [{str}, {int}])
        #try:
            #self.socket.connect((addr, port))
            #self.socket.setblocking(False)
        #except Exception as e:
            #if e.args[0] != 10035:
                #raise e
            #else:
                #utils.showWarning("DEBUG", e)
    #def startMain(self):
        #self.mainThread = utils.Thread(target=self.mainLoop)
        #self.mainThread.start()
    #def abort(self):
        #self.mainThread.stop()
        #self.socket.close()
    #def _send(self, msg):
        #utils.checkParamTypes("network.Client.send", [msg], [{bytes}])
        #self.sendQueue += msg
    #def _popSendQueue(self, length):
        #buf = self.sendQueue[:length]
        #self.sendQueue = send.recvQueue[length:]
        #return buf    
    #def _popRecvQueue(self, length):
        #buf = self.recvQueue[:length]
        #self.recvQueue = self.recvQueue[length:]
        #return buf
    #def _recv(self, length):
        ## TODO: Timeout?
        #buf = b''
        #sTime = time.process_time()
        #while time.process_time() - sTime < 15 and len(buf) < length: # Port to config
            #if len(self.recvQueue) > 0:
                #buf += self._popRecvQueue(min(length - len(buf), len(self.recvQueue)))
        #if len(buf) < length:
            #self.recvQueue = buf + self.recvQueue
            #utils.raiseException("network.Client._recv", "Not enough data to recieve")
        #return buf
    #def recievePacket(self):
        ## TODO: parse packet; await packet completion; decypher packet; fix this shit)
        #EPID = int.from_bytes(self._recv(1), "big")
        #EPSIZE = int.from_bytes(self._recv(2), "big")
        #EPDATA = self._recv(ESIZE)
        #return EPID, EPDATA
    #def mainLoop(self):
        #while not self.mainThread.stopped:
            #if len(self.sendQueue) > 0:
                #try:
                    #c.send(self._popSendQueue(128))
                #except Exception as e:
                    #if e.args[0] != 10035:
                        #utils.ShowWarning("network.Client.mainLoop", e)
            #time.sleep(0.5)
            #try:
                #self.recvQueue += c.recv(128)
            #except Exception as e:
                #if e.args[0] != 10035:
                    #utils.ShowWarning("network.Client.mainLoop", e)

#class Server:
    #def __init__(self):
        #self.socket = socket.socket()
        ##self.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
        #self.clients = dict()
        #self.mainThread = None
    #def listen(self, addr="", port=-1):
        #utils.checkParamTypes("network.Server.listen", [addr, port], [{str}, {int}])
        #if port == -1:
            #port = int(config.getValue("Network", "DefaultPort", "8887"))
        #self.socket.bind((addr, port))
        #self.socket.listen(int(config.getValue("Network", "MaxConnections", "15")))
    #def startMain(self):
        #self.mainThread = utils.Thread(target=self.mainLoop)
        #self.mainThread.start()
    #def abort(self):
        #self.mainThread.stop()
        #for addr in self.clients:
            #self.clients[addr].abort()
        #self.socket.close()
    #def wrapClientObject(self, cl):
        #utils.checkParamTypes("network.Server.createClientThread", [cl], [{socket.socket}])
        #client = Client()
        #client.socket = cl
        ##client.socket.settimeout(int(config.getValue("Network", "Timeout", "2000")) / 1000)
        #client.socket.setblocking(False)
        #client.startMain()
        #return client
    #def mainLoop(self):
        #while not self.mainThread.stopped():
            ## TODO: Close dead ones
            #try:
                #cl, addr = self.socket.accept()
                #if addr in self.clients:
                    #utils.showWarning("network.Server.mainLoop", "Present client tries to connect again from the same ip ({})".format(addr))
                #else:
                    #self.clients[addr] = self.wrapClientObject(cl)
            #except Exception as e:
                #print(e)
                #pass