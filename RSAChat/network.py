import socket
import socketserver
import asyncio
import hashlib
from collections import deque
import time
from . import utils
from . import protocol
from . import RSA
from . import messaging


class RoutingTable(dict):
    def initialize(self, key):
        if key in self:
            return
        self[key] = deque()
    
    def put(self, key, value):
        self.initialize(key)  # ?
        self[key].append(value)
    
    def get(self, key, blocking=False):
        lQueue = self[key]
        while blocking and len(lQueue) == 0:
            pass
        if len(lQueue) == 0:
            raise utils.NotEnoughDataException()
        return lQueue.popleft()
    
    def len(self, key):
        return len(self[key])  # ?
    
    def clear(self, key):
        # ? Delete or make blank?
        if key in self:
            del self[key]


class ServerInitialHandler(socketserver.StreamRequestHandler):
    def __init__(self, aServerKey, aRoutingTable, *args, **kwargs):
        self.serverKey = aServerKey
        self.routingTable = aRoutingTable
        super().__init__(*args, **kwargs)
    
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
        lClientPKey, lSessionID = lHshP.execute()
        
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
    def __init__(self, aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs):
        self.selfKey = aSelfKey
        self.otherPKey = aOtherPKey
        self.sessionID = aSessionID
        # ? Got to be awaited/executed in loop
        asyncio.gather(*[self.__getattribute__(i)() for i in dir(self) if i.startswith("background_")], loop=aLoop)
        self.connected = aLoop.create_future()
        self.disconnected = aLoop.create_future()
        super().__init__(*args, **kwargs)
    
    def connection_made(self, transport):
        self.transport = transport
        self.recvBuf = utils.Buffer()
        self.connected.set_result(True)
    
    def send(self, data):  # add some form of awaiting?
        #utils.log("[->]", data)
        self.transport.write(data)
    
    def recv(self, n):
        return self.recvBuf.get(n)
    
    def data_received(self, data):
        #utils.log('[<-]', data)
        self.recvBuf.put(data)
        
    def connection_lost(self, exc=None):
        self.transport.close()  # ?
        self.disconnected.set_result(True)


class ServerGeneralProtocol(BaseGeneralProtocol):
    def __init__(self, aRoutingTable, aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs):
        self.routingTable = aRoutingTable
        self.routingTable.initialize(aOtherPKey)
        super().__init__(aLoop, aSelfKey, aOtherPKey, aSessionID, *args, **kwargs)
    
    def connection_made(self, transport):
        utils.log("General phase")
        super().connection_made(transport)
    
    async def background_incoming(self):
        await self.connected
        while True:
            #utils.log("Server in")
            await asyncio.sleep(0)
            try:
                lEPacket = protocol.REGULAR_PACKET.receive(self.recv)
            except utils.NotEnoughDataException:
                continue
            lSPacket = lEPacket.get_EPDATA(self.selfKey)
            assert lSPacket.get_SPSID() == self.sessionID
            lRecepient = lSPacket.get_SPKEY()
            lSPacket.SPKEY = utils.dumpRSAKey(self.otherPKey, PUB=True).encode()
            self.routingTable.put(lRecepient, lSPacket)
            utils.log("[*] Message from:\n{}\nTo:\n{}\n[*]".format(utils.dumpRSAKey(self.otherPKey, PUB=True), utils.dumpRSAKey(lRecepient, PUB=True)))
    
    async def background_outgoing(self):
        await self.connected
        while True:
            #utils.log("Server out")
            await asyncio.sleep(0)
            try:
                lSPacket = self.routingTable.get(self.otherPKey)
            except utils.NotEnoughDataException:
                continue
            lSPacket.SPSID = self.sessionID
            self.send(protocol.REGULAR_PACKET.build(lSPacket, self.otherPKey).encode())

    def connection_lost(self, exc=None):
        utils.log("Disconnect")
        super().connection_lost(exc=exc)


class ClientGeneralProtocol(BaseGeneralProtocol):
    def connection_made(self, transport):
        utils.log("Connected to {0[0]}:{0[1]}".format(transport._sock.getpeername()))
        super().connection_made(transport)
    
    async def background_incoming(self):
        await self.connected
        while True:
            #utils.log("Client in")
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
            utils.log(lSender, lPPacket)
    
    async def background_outgoing(self):
        await self.connected
        while True:  # TODO: Finish
            #utils.log("Client out")
            await asyncio.sleep(0)
            try:
                pass # Get msg
            except utils.NotEnoughDataException:
                continue
            lRecepient = self.selfKey.getPublicKey()
            lMessage = "Hello"
            lPPacket = protocol.PPACKET.build(lMessage, self.selfKey)
            lSPacket = protocol.SPACKET.build(lPPacket, lRecepient, self.sessionID)
            lEPacket = protocol.REGULAR_PACKET.build(lSPacket, self.otherPKey)
            self.send(lEPacket.encode())
            utils.log("Sending...")
            return

    def connection_lost(self, exc=None):
        utils.log("Disconnect")
        super().connection_lost(exc=exc)


def start_server(host="", port=8887, aServerKey=None):
    serverKey = utils.loadRSAKey(aServerKey, PRIV=True) if aServerKey is not None else RSA.genKeyPair()[1]
    routingTable = RoutingTable()
    with socketserver.ThreadingTCPServer((host, port), (lambda *args, **kwargs: ServerInitialHandler(serverKey, routingTable, *args, **kwargs))) as serv:
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