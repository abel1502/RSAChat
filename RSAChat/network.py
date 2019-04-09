import socket, socketserver
from . import utils
from . import config
from collections import deque
import time
import asyncio
from . import protocol
from . import RSA

PACKET_SIZE = int(config.getValue("Network", "Packet_Size", "4096"))
SERVER = None
CLIENT = None
SENDBUF = {} # Public key -> send packet queue


class Server:
    def __init__(self, host="", port=8887, privKey=None):
        self.eventLoop = asyncio.get_event_loop()
        coro = self.eventLoop.create_server(ServerProtocol, host, port)
        self.aioServer = self.eventLoop.run_until_complete(coro)
        self.clients = []
        self.privKey = privKey if privKey is not None else RSA.genKeyPair()[1]
        global SERVER
        SERVER = self
    def start(self):
        utils.startThread(self.eventLoop.run_forever)
    def abort(self):
        self.eventLoop.call_soon_threadsafe(self.eventLoop.stop)
        self.aioServer.close()
        self.eventLoop.call_soon_threadsafe(self.eventLoop.close)
        global SERVER
        SERVER = None

class ServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        print("Someone connected")
        self.transport = transport
        self.recvBuf = b''
        self.curPacket = protocol.EPACKET()
        self.packets = deque()
        global SERVER
        SERVER.clients.append(self)
        self.mainThread = utils.Thread(target=self.handlePackets)
        self.mainThread.start()
        #self.stage = 0 # 0, 1,  - handshake
        self.clPublicKey = None
        self.clPublicKeyVerified = False
    def sendPacket(self, packet):
        # TODO: Temporary?
        pass
    def handlePackets(self):
        while not self.mainThread.stopped():
            #print('.1', list(self.packets))
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print("[*]", packet.EPID, packet.EPLEN, packet.EPDATA)
        global SERVER
        if self.clPublicKey is None:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_CL_ASK:
                # TODO: Verify
                self.clPublicKey = RSA.PublicKey.load(packet.EPDATA.decode())
                self.sendPacket(protocol.EPACKET(protocol.EPACKET_TYPE.HSH_SRV_ANS, -1, self.clPublicKey.encrypt(SERVER.privKey.getPublicKey.dump())))
            elif packet.EPID == protocol.EPACKET_TYPE.HSH_CL_SIMPLE:
                # TODO: Verify again
                self.clPublicKey = RSA.PublicKey.load(self.PrivateKey.decrypt(packet.EPDATA))
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        elif not self.clPublicKeyVerified:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_VER_ANS:
                pass
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        else:
            # TODO: Normal packet handling
            pass
    def data_received(self, data):
        #print('[*]', data)
        self.recvBuf += data
        self.recvBuf, success = self.curPacket.parse(self.recvBuf)
        while success:
            self.packets.append(self.curPacket)
            self.curPacket = protocol.EPACKET()
            self.recvBuf, success = self.curPacket.parse(self.recvBuf)
    def connection_lost(self, exc):
        self.mainThread.stop()
        self.transport.close()


class Client:
    def __init__(self, host, port=8887):
        global CLIENT
        CLIENT = self
        self.eventLoop = asyncio.get_event_loop()
        coro = self.eventLoop.create_connection(ClientProtocol, host, port)
        self.aioClient = self.eventLoop.run_until_complete(coro)
        self.protocol = None
    def start(self):
        utils.startThread(self.eventLoop.run_forever)
    def abort(self):
        self.eventLoop.call_soon_threadsafe(self.eventLoop.stop)
        # It works for shutdown... I guess)
        self.aioClient[1].connection_lost(None)
        self.aioClient[0].close()
        self.eventLoop.call_soon_threadsafe(self.eventLoop)
        time.sleep(1)
        global CLIENT
        CLIENT = None


class ClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.recvBuf = b''
        self.curPacket = protocol.EPACKET()
        self.packets = deque()
        # The first doesn't work, for some reason
        #global CLIENT
        #CLIENT.protocol = self
        #global CLIENT_PROTOCOL
        #CLIENT_PROTOCOL = self
        self.mainThread = utils.Thread(target=self.handlePackets)
        self.mainThread.start()
    def handlePackets(self):
        while not self.mainThread.stopped():
            print('.1')
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print(packet.EPID, packet.EPLEN, packet.EPDATA)
    def data_received(self, data):
        print('[*]', data)
        self.recvBuf += data
        self.recvBuf, success = self.curPacket.parse(self.recvBuf)
        while success:
            self.packets.append(self.curPacket)
            self.curPacket = protocol.EPACKET()
            self.recvBuf, success = self.curPacket.parse(self.recvBuf)
    def connection_lost(self, exc):
        self.mainThread.stop()
        self.transport.close()


#def addClientToServer(cl):
    #if SERVER is not None:
        #SERVER.clients.append(cl)


#def startServer(host="", port=8887):
    #SERVER = Server(host, port)
    #SERVER.start()


#class Server:
    #def __init__(self, host="", port=8887):
        #self.eventLoop = asyncio.get_event_loop()
        #coro = self.eventLoop.create_server(ServerProtocol, host, port)
        #self.aioServer = self.eventLoop.run_until_complete(coro)
        #self.clients = []  # Dict?....
    #def start(self):
        #utils.startThread(self.eventLoop.run_forever)
    #def abort(self):
        ## TODO: Close clients
        #self.aioServer.close()
        #self.eventLoop.stop()
        #self.eventLoop.close()


#class ServerProtocol(asyncio.Protocol):
    #def send(self, data):
        #self.transport.write(data)
    #def recv(self, length):
        #buf = self.recvBuf[:length]
        #self.recvBuf = self.recvBuf[length:]
        #return buf
    #def connection_made(self, transport):
        #peername = transport.get_extra_info('peername')
        ##print('Connection from {}'.format(peername))
        #self.transport = transport
        #addClientToServer(self)
        #self.recvBuf = b''
    #def data_received(self, data):
        #self.recvBuf += data


#class Client:
    #def __init__(self, host, port=8887):
        #self.eventLoop = asyncio.get_event_loop()
        #coro = self.eventLoop.create_connection(lambda: ClientProtocol(self.eventLoop), host, port)
        #self.aioClient = self.eventLoop.run_until_complete(coro)
    #def send(self, data):
        #self.aioClient.send(data)
    #def recv(self, length):
        #return self.aioClient.recv(length)
    #def start(self):
        #utils.startThread(self.eventLoop.run_forever)
    #def abort(self):
        #self.aioClient.close()
        #self.eventLoop.stop()
        #self.eventLoop.close()    


#class ClientProtocol(asyncio.Protocol):
    #def __init__(self, loop):
        #self.loop = loop
    #def send(self, data):
        #self.transport.write(data)
    #def recv(self, length):
        #buf = self.recvBuf[:length]
        #self.recvBuf = self.recvBuf[length:]
        #return buf
    #def close(self):
        #self.transport.close()
        #self.loop.stop()
    #def connection_made(self, transport):
        #self.transport = transport
        #self.recvBuf = b''
    #def data_received(self, data):
        #self.recvBuf += data
    #def connection_lost(self, exc):
        #self.loop.stop()


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