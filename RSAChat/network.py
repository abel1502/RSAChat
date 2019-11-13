import socket
import socketserver
import asyncio
import hashlib
from collections import deque
from weakref import WeakSet
import time
from . import utils
from . import protocol
from . import RSA
from . import messaging

MAX_CONNECTIONS = 64


class RoutingTable(dict):
    def __init__(self, *args, **kwargs):
        self._connected = 0
        super().__init__(*args, **kwargs)
    
    def getConnected(self):
        return self._connected
    
    def initialize(self, key):
        if key in self:
            return
        self[key] = [deque(), False]
    
    def logOn(self, key):
        self[key][1] = True
        self._connected += 1
    
    def logOff(self, key):
        self[key][1] = False
        self._connected -= 1
    
    def isOnline(self, key):
        return self[key][1]
    
    def put(self, key, value):
        self.initialize(key)  # ?
        self[key][0].append(value)
    
    def get(self, key, blocking=False):
        lQueue = self[key][0]
        while blocking and len(lQueue) == 0:
            pass
        if len(lQueue) == 0:
            raise utils.NotEnoughDataException()
        return lQueue.popleft()
    
    def getEveryone(self, online=False):
        lRes = self.keys()
        if online:
            return [i for i in lRes if self.isOnline(i)]
        return lRes
    
    def len(self, key):
        return len(self[key][0])  # ?
    
    def clear(self, key):
        # ? Delete or make blank?
        if key in self:
            del self[key]


class ServerInitialHandler(socketserver.StreamRequestHandler):
    def __init__(self, aServerKey, aRoutingTable, aActiveConnections, *args, **kwargs):
        self.serverKey = aServerKey
        self.routingTable = aRoutingTable
        self.activeConnections = aActiveConnections
        super().__init__(*args, **kwargs)
    
    def isOverloaded(self):  # ? Needs some testing
        return len(self.activeConnections) > MAX_CONNECTIONS
    
    def recv(self, n):
        lBuf = utils.Buffer()
        while n - len(lBuf) > 0:
            lBuf.put(self.rfile.read(n - len(lBuf)))
        return lBuf.getAll()
    
    def send(self, data):
        self.wfile.write(data)
    
    def handle(self):
        utils.log("Connection from {0[0]}:{0[1]}".format(self.request.getpeername()))
        # TODO: Timeout and check for shutdown?
        
        lHshP = protocol.ServerHandshakeProtocol(self.send, self.recv, self.serverKey)
        lClientPKey, lSessionID = lHshP.execute(overloaded=self.isOverloaded())
        self.activeConnections.add(self.request)
        
        lLoop = asyncio.new_event_loop() # ?
        lTransport, lServerGeneralProtocol = lLoop.run_until_complete(lLoop.connect_accepted_socket(lambda *args, **kwargs: ServerGeneralProtocol(self.routingTable, lLoop, self.serverKey, lClientPKey, lSessionID, *args, **kwargs), self.request))
        try:
            lLoop.run_until_complete(lServerGeneralProtocol.disconnected)
        except KeyboardInterrupt:
            pass
        finally:
            lTransport.close()
            lLoop.close()


class BaseGeneralProtocol(asyncio.Protocol):
    logWithSID = False
    sessionFlair = "[{}]"
    
    def __init__(self, aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs):
        self.selfKey = aSelfKey
        self.otherPKey = aOtherPKey
        self.sessionID = aSessionID
        # ? Got to be awaited/executed in loop
        asyncio.gather(*[self.__getattribute__(i)() for i in dir(self) if i.startswith("background_")], loop=aLoop)
        self.connected = aLoop.create_future()
        self.disconnected = aLoop.create_future()
        super().__init__(*args, **kwargs)
    
    def log(self, *data, withSID=None):
        if withSID is None:
            withSID = self.logWithSID
        if withSID:
            lSessionMarker = self.sessionFalir.format(self.sessionID.hex())
            utils.log(lSessionMarker, *data)
        else:
            utils.log(*data)
    
    def connection_made(self, transport):
        self.transport = transport
        self.recvBuf = utils.Buffer()
        self.connected.set_result(True)
    
    def send(self, data):  # add some form of awaiting?
        #self.log("[->]", data)
        self.transport.write(data)
    
    def recv(self, n):
        return self.recvBuf.get(n)
    
    def data_received(self, data):
        #self.log('[<-]', data)
        self.recvBuf.put(data)
        
    def connection_lost(self, exc=None):
        self.transport.close()  # ?
        self.disconnected.set_result(True)


class ServerGeneralProtocol(BaseGeneralProtocol):
    logWithSID = True
    sessionFalir = utils.wrapCsi("[{}]", 96)
    
    def __init__(self, aRoutingTable, aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs):
        self.routingTable = aRoutingTable
        self.routingTable.initialize(aOtherPKey)
        assert not self.routingTable.isOnline(aOtherPKey)
        super().__init__(aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs)
    
    def connection_made(self, transport):
        self.log("[+] Identified {}".format(self.otherPKey.getReprName()))
        self.routingTable.logOn(self.otherPKey)
        super().connection_made(transport)
    
    async def background_incoming(self):
        await self.connected
        while True:
            #self.log("Server in")
            await asyncio.sleep(0)
            try:
                lEPacket = protocol.REGULAR_PACKET.receive(self.recv)
            except utils.NotEnoughDataException:
                continue
            lSPacket = lEPacket.get_EPDATA(self.selfKey)
            assert lSPacket.get_SPSID() == self.sessionID
            lRecepient = lSPacket.get_SPKEY()
            if lRecepient == self.selfKey.getPublicKey():
                for lMember in self.routingTable.getEveryone(online=True):
                    lNewSPacket = protocol.SPACKET.build(lSPacket.get_SPDATA(self.selfKey), lMember, self.sessionID)
                    lNewSPacket.SPKEY = utils.dumpRSAKey(self.otherPKey, PUB=True).encode()
                    self.routingTable.put(lMember, lNewSPacket)
                self.log("[*] Message from:\n{}\nTo: Everyone".format(self.otherPKey.getReprName()))
            else:
                lNewSPacket = protocol.SPACKET.copy(lSPacket)
                lNewSPacket.SPKEY = utils.dumpRSAKey(self.otherPKey, PUB=True).encode()
                self.routingTable.put(lRecepient, lNewSPacket)
                self.log("[*] Message from:\n{}\nTo:\n{}".format(self.otherPKey.getReprName(), lRecepient.getReprName()))
    
    async def background_outgoing(self):
        await self.connected
        while True:
            #self.log("Server out")
            await asyncio.sleep(0)
            try:
                lSPacket = self.routingTable.get(self.otherPKey)
            except utils.NotEnoughDataException:
                continue
            lSPacket.SPSID = self.sessionID
            self.send(protocol.REGULAR_PACKET.build(lSPacket, self.otherPKey).encode())

    def connection_lost(self, exc=None):
        self.log("[-] Disconnected")
        self.routingTable.logOff(self.otherPKey)
        super().connection_lost(exc=exc)


class ClientGeneralProtocol(BaseGeneralProtocol):
    def connection_made(self, transport):
        self.log("Connected to {0[0]}:{0[1]}".format(transport._sock.getpeername()))
        self.console = messaging.start_console()
        self.console.setIdentity(self.selfKey.getPublicKey())
        self.console.tmp(self.otherPKey)
        super().connection_made(transport)
    
    async def background_incoming(self):
        await self.connected
        while True:
            #self.log("Client in")
            await asyncio.sleep(0)
            try:
                lEPacket = protocol.REGULAR_PACKET.receive(self.recv)
            except utils.NotEnoughDataException:
                continue
            lSPacket = lEPacket.get_EPDATA(self.selfKey)
            assert lSPacket.get_SPSID() == self.sessionID
            lSender = lSPacket.get_SPKEY()
            lPPacket = lSPacket.get_SPDATA(self.selfKey)
            assert lPPacket.verify(lSender)
            lMessage = messaging.Message.fromPPacket(lPPacket, lSender, self.selfKey.getPublicKey())
            self.console.addIncoming(lMessage)
    
    async def background_outgoing(self):
        await self.connected
        while True:
            #self.log("Client out")
            await asyncio.sleep(0)
            try:
                lMsg = self.console.getOutgoing()
                lRecepient = lMsg.recepient
            except utils.NotEnoughDataException:
                continue
            #lText = "My name is Yoshikage Kira. I'm 33 years old. My house is in the northeast section of Morioh, where all the villas are, and I am not married. I work as an employee for the Kame Yu department stores, and I get home every day by 8 PM at the latest. I don't smoke, but I ocassionaly drink. I'm in bed by 11 PM, and make sure I get eight hours of sleep, no matter what. After having a glass of warm milk and doing about twenty minutes of stretches before going to bed, I usually have no problems sleeping until morning. Just like a baby, I wake up without any fatigue or stress in the morning. I was told there were no issues at my last check-up. I'm trying to explain that I'm a person who wishes to live a very quiet life. I take care not to trouble myself with any enemies, like winning and losing, that would cause me to lose sleep at night. That is how I deal with society, and I know that is what brings me happiness. Althought, if I were to fight I wouldn't lose to anyone."
            #lRecepient = self.selfKey.getPublicKey()
            #lMsg = messaging.Message(lText, self.selfKey.getPublicKey(), lRecepient)
            lPPacket = lMsg.toPPacket(self.selfKey)
            lSPacket = protocol.SPACKET.build(lPPacket, lRecepient, self.sessionID)
            lEPacket = protocol.REGULAR_PACKET.build(lSPacket, self.otherPKey)
            self.send(lEPacket.encode())
            #self.log("Sending...")

    def connection_lost(self, exc=None):
        self.log("Disconnect")
        super().connection_lost(exc=exc)


def start_server(host="", port=8887, aServerKey=None):
    serverKey = utils.loadRSAKey(aServerKey, PRIV=True) if aServerKey is not None else RSA.genKeyPair()[1]
    routingTable = RoutingTable()
    activeConnections = WeakSet()
    with socketserver.ThreadingTCPServer((host, port), (lambda *args, **kwargs: ServerInitialHandler(serverKey, routingTable, activeConnections, *args, **kwargs))) as serv:
        serv.serve_forever()
    serv.close()  # ?


def connect_client(host, port=8887, aClientKey=None, aServerPKey=None):    
    lClientKey = utils.loadRSAKey(aClientKey, PRIV=True) if aClientKey is not None else RSA.genKeyPair()[1]
    lClientSocket = socket.create_connection((host, port))
    
    def _recv(n):
        lBuf = utils.Buffer()
        while n - len(lBuf) > 0:
            lBuf.put(lClientSocket.recv(n - len(lBuf)))
        return lBuf.getAll()
    
    def _send(data):
        lClientSocket.sendall(data)
    
    lHshP = protocol.ClientHandshakeProtocol(_send, _recv, aClientKey)  # ?
    lServerPKey, lSessionID = lHshP.execute(aServerPKey)
    
    lLoop = asyncio.get_event_loop() # ?
    lTransport, lClientGeneralProtocol = lLoop.run_until_complete(lLoop.create_connection(lambda *args, **kwargs: ClientGeneralProtocol(lLoop, lClientKey, lServerPKey, lSessionID, *args, **kwargs), sock=lClientSocket))
    try:
        lLoop.run_until_complete(lClientGeneralProtocol.disconnected)
    except KeyboardInterrupt:
        pass
    finally:
        lTransport.close()
        lLoop.close()