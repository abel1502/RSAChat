import socket
import socketserver
import asyncio
import hashlib
from collections import deque
#from queue import Queue
from weakref import WeakSet
import time
import re
from RSAChat import utils
from RSAChat import protocol
from RSAChat import messaging

MAX_CONNECTIONS = 64


class RoutingUnit:
    def __init__(self, key, nickname=None):
        self.key = key
        self.queue = deque()
        self.online = False
        self.nickname = nickname


class RoutingTable(dict):
    def __init__(self, *args, **kwargs):
        self._connected = 0
        super().__init__(*args, **kwargs)
    
    def getConnected(self):
        return self._connected
    
    def initialize(self, key, nickname=None):
        if key in self:
            return
        self[key] = RoutingUnit(key, nickname=nickname)
    
    def logOn(self, key):
        self[key].online = True
        self._connected += 1
    
    def logOff(self, key):
        self[key].online = False
        self._connected -= 1
    
    def isOnline(self, key):
        return self[key].online
    
    def put(self, key, value):
        self.initialize(key)  # ?
        self[key].queue.append(value)
    
    def get(self, key, blocking=False):
        lQueue = self[key].queue
        while blocking and len(lQueue) == 0:
            pass
        if len(lQueue) == 0:
            raise utils.NotEnoughDataException()
        return lQueue.popleft()
    
    def getEveryone(self, online=False):
        lRes = self.keys()
        if online:
            return [self[i] for i in lRes if self.isOnline(i)]
        return [self[i] for i in lRes]
    
    def len(self, key):
        return len(self[key].queue)  # ?
    
    def clear(self, key):
        # ? Delete or make blank?
        if key in self:
            del self[key]


class ResponseData:
    def __init__(self, type):
        self.finished = False
        self.type = type
        self.value = None
    
    def respond(self, value):
        self.value = value
        self.finished = True


class ResponseContainer(dict):
    def request(self, type, respId=None):
        if respId is None:
            respId = self.allocateRespId(blocking=True)
        if respId in self:
            assert False
        self[respId] = ResponseData(type)
        return respId
    
    def respond(self, respId, value):
        self[respId].respond(value)
    
    def awaits(self, respId):
        return respId in self and not self[respId].finished
    
    def finished(self, respId):
        return self[respId].finished
    
    def getResponse(self, respId, blocking=False):
        while blocking and not self[respId].finished:
            pass
        if not self[respId].finished:
            raise utils.NotEnoughDataException()
        return self[respId].value
    
    def allocateRespId(self, blocking=False):
        while blocking and len(self.keys()) > 65535:
            pass
        lIds = set(self.keys())
        for i in range(65536):
            if i not in lIds:
                return i
        raise utils.NotEnoughDataException()
    
    def clear(self, respId):
        if respId in self:
            del self[respId]


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
        lClientPKey, lClientNickname, lSessionID = lHshP.execute(overloaded=self.isOverloaded())
        self.activeConnections.add(self.request)
        
        lLoop = asyncio.new_event_loop() # ?
        lTransport, lServerGeneralProtocol = lLoop.run_until_complete(lLoop.connect_accepted_socket(lambda *args, **kwargs: ServerGeneralProtocol(self.routingTable, lLoop, self.serverKey, lClientPKey, lClientNickname, lSessionID, *args, **kwargs), self.request))
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
    
    def __init__(self, aLoop, aSelfKey, aOtherPKey, aNickname, aSessionID, *args, **kwargs):
        self.selfKey = aSelfKey
        self.otherPKey = aOtherPKey
        self.nickname = aNickname
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
            lSessionMarker = self.sessionFlair.format(self.sessionID.hex())
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
    sessionFlair = utils.ColorProvider.getInstance().wrap("[{}]", 96)
    
    def __init__(self, aRoutingTable, aLoop, aSelfKey, aOtherPKey, aNickname, aSessionID, *args, **kwargs):
        self.routingTable = aRoutingTable
        self.routingTable.initialize(aOtherPKey, nickname=aNickname)
        assert not self.routingTable.isOnline(aOtherPKey)
        super().__init__(aLoop, aSelfKey, aOtherPKey, aNickname, aSessionID, *args, **kwargs)
    
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
                lEPacket = protocol.REGULAR_EPACKET.receive(self.recv).INNER
            except utils.NotEnoughDataException:
                continue
            lSPacket = lEPacket.get_EPDATA(self.selfKey)
            assert lSPacket.verifySession(self.sessionID)
            lSPacket = lSPacket.INNER
            if isinstance(lSPacket, protocol.MESSAGE_SPACKET):
                self.handleMessagePacket(lSPacket)
            elif isinstance(lSPacket, protocol.LOOKUP_ASK_SPACKET):
                self.handleLookupPacket(lSPacket)
            elif isinstance(lSPacket, protocol.ONLINE_ASK_SPACKET):
                self.handleOnlinePacket(lSPacket)
            else:
                assert False
    
    def handleMessagePacket(self, packet):
        lRecepient = packet.get_SPKEY()
        if lRecepient == self.selfKey.getPublicKey():
            for lMember in self.routingTable.getEveryone(online=True):
                lNewSPacket = protocol.MESSAGE_SPACKET.build(packet.get_SPDATA(self.selfKey), lMember.key)
                lNewSPacket.SPKEY = utils.RSA.dumpKey(self.otherPKey, PUB=True).encode()
                self.routingTable.put(lMember.key, lNewSPacket)
            self.log("[*] Message from:\n{}\nTo: Everyone".format(self.otherPKey.getReprName()))
        else:
            lNewSPacket = packet.copy()
            lNewSPacket.SPKEY = utils.RSA.dumpKey(self.otherPKey, PUB=True).encode()
            self.routingTable.put(lRecepient, lNewSPacket)
            self.log("[*] Message from:\n{}\nTo:\n{}".format(self.otherPKey.getReprName(), lRecepient.getReprName()))
    
    def handleLookupPacket(self, packet):
        lTarget = packet.get_SPTARGET()
        assert re.fullmatch(utils.RSA.nicknamePattern, lTarget)
        lResults = [i.key for i in self.routingTable.getEveryone(online=True) if i.nickname == lTarget]
        if len(lResults) == 0:
            lResults = [None]
        assert len(lResults) == 1
        self.routingTable.put(self.otherPKey, protocol.LOOKUP_ANS_SPACKET.build(packet.SPRID, lResults[0]))
    
    def handleOnlinePacket(self, packet):
        # TODO: !Prevent overflows!
        lResults = [str(i.nickname) for i in self.routingTable.getEveryone(online=True) if i.nickname is not None]
        self.routingTable.put(self.otherPKey, protocol.ONLINE_ANS_SPACKET.build(packet.SPRID, lResults))
    
    async def background_outgoing(self):
        await self.connected
        while True:
            #self.log("Server out")
            await asyncio.sleep(0)
            try:
                lSPacket = self.routingTable.get(self.otherPKey)
            except utils.NotEnoughDataException:
                continue
            lSPacket = protocol.SPACKET.build(lSPacket, self.sessionID)
            self.send(protocol.EPACKET.build(protocol.REGULAR_EPACKET.build(lSPacket, self.otherPKey)).encode())

    def connection_lost(self, exc=None):
        self.log("[-] Disconnected")
        self.routingTable.logOff(self.otherPKey)
        super().connection_lost(exc=exc)


class ClientGeneralProtocol(BaseGeneralProtocol):
    def connection_made(self, transport):
        self.log("Connected to {0[0]}:{0[1]}".format(transport._sock.getpeername()))
        self.console = messaging.start_console(self)
        self.console.setIdentity(self.selfKey.getPublicKey())
        self.respContainer = ResponseContainer()
        self.outgoingQueue = deque()
        super().connection_made(transport)
    
    async def background_incoming(self):
        await self.connected
        while True:
            #self.log("Client in")
            await asyncio.sleep(0)
            try:
                lEPacket = protocol.REGULAR_EPACKET.receive(self.recv).INNER
            except utils.NotEnoughDataException:
                continue
            lSPacket = lEPacket.get_EPDATA(self.selfKey)
            assert lSPacket.verifySession(self.sessionID)
            lSPacket = lSPacket.INNER
            if isinstance(lSPacket, protocol.MESSAGE_SPACKET):
                self.handleMessagePacket(lSPacket)
            elif isinstance(lSPacket, protocol.LOOKUP_ANS_SPACKET):
                self.handleLookupPacket(lSPacket)
            elif isinstance(lSPacket, protocol.ONLINE_ANS_SPACKET):
                self.handleOnlinePacket(lSPacket)
            else:
                assert False
    
    def handleMessagePacket(self, packet):
        lSender = packet.get_SPKEY()
        lPPacket = packet.get_SPDATA(self.selfKey)
        assert lPPacket.verify(lSender)
        lMessage = messaging.Message.fromPPacket(lPPacket, lSender, self.selfKey.getPublicKey())
        self.console.addIncoming(lMessage)
    
    def handleLookupPacket(self, packet):
        assert self.respContainer.awaits(packet.SPRID)
        assert self.respContainer[packet.SPRID].type == "LOOKUP"
        self.respContainer.respond(packet.SPRID, packet.get_SPKEY())
    
    def handleOnlinePacket(self, packet):
        assert self.respContainer.awaits(packet.SPRID)
        assert self.respContainer[packet.SPRID].type == "ONLINE"
        self.respContainer.respond(packet.SPRID, packet.get_SPONLINE())
    
    async def background_outgoing(self):
        await self.connected
        while True:
            #self.log("Client out")
            await asyncio.sleep(0)
            try:
                lSPacket = utils.queueGet(self.outgoingQueue)
            except utils.NotEnoughDataException:
                continue
            #lText = "My name is Yoshikage Kira. I'm 33 years old. My house is in the northeast section of Morioh, where all the villas are, and I am not married. I work as an employee for the Kame Yu department stores, and I get home every day by 8 PM at the latest. I don't smoke, but I ocassionaly drink. I'm in bed by 11 PM, and make sure I get eight hours of sleep, no matter what. After having a glass of warm milk and doing about twenty minutes of stretches before going to bed, I usually have no problems sleeping until morning. Just like a baby, I wake up without any fatigue or stress in the morning. I was told there were no issues at my last check-up. I'm trying to explain that I'm a person who wishes to live a very quiet life. I take care not to trouble myself with any enemies, like winning and losing, that would cause me to lose sleep at night. That is how I deal with society, and I know that is what brings me happiness. Althought, if I were to fight I wouldn't lose to anyone."
            #lRecepient = self.selfKey.getPublicKey()
            #lMsg = messaging.Message(lText, self.selfKey.getPublicKey(), lRecepient)
            lSPacket = protocol.SPACKET.build(lSPacket, self.sessionID)
            lEPacket = protocol.EPACKET.build(protocol.REGULAR_EPACKET.build(lSPacket, self.otherPKey))
            self.send(lEPacket.encode())
            #self.log("Sending...")
    
    def queueSend(self, packet):
        self.outgoingQueue.append(packet)
    
    def sendMessage(self, msg):
        if msg.recepient is None:
            msg.recepient = self.otherPKey
        lPPacket = msg.toPPacket(self.selfKey)
        lSPacket = protocol.MESSAGE_SPACKET.build(lPPacket, msg.recepient)
        self.queueSend(lSPacket)
    
    def sendLookup(self, target):
        respId = self.respContainer.request("LOOKUP")
        lSPacket = protocol.LOOKUP_ASK_SPACKET.build(respId, target)
        self.queueSend(lSPacket)
        lPKey = self.respContainer.getResponse(respId, blocking=True)
        return lPKey
    
    def sendOnline(self):
        respId = self.respContainer.request("ONLINE")
        lSPacket = protocol.ONLINE_ASK_SPACKET.build(respId)
        self.queueSend(lSPacket)
        lOnline = self.respContainer.getResponse(respId, blocking=True)
        return lOnline
    
    def connection_lost(self, exc=None):
        self.log("Disconnect")
        super().connection_lost(exc=exc)


def start_server(host="", port=8887, aServerKey=None):
    serverKey = utils.RSA.loadKey(aServerKey, PRIV=True) if aServerKey is not None else RSA.genKeyPair()[1]
    routingTable = RoutingTable()
    activeConnections = WeakSet()
    with socketserver.ThreadingTCPServer((host, port), (lambda *args, **kwargs: ServerInitialHandler(serverKey, routingTable, activeConnections, *args, **kwargs))) as serv:
        serv.serve_forever()
    serv.close()  # ?


def connect_client(host, port=8887, aClientKey=None, aServerPKey=None, aNickname=None):    
    lClientKey = utils.RSA.loadKey(aClientKey, PRIV=True) if aClientKey is not None else RSA.genKeyPair()[1]
    lClientSocket = socket.create_connection((host, port))
    
    def _recv(n):
        lBuf = utils.Buffer()
        while n - len(lBuf) > 0:
            lBuf.put(lClientSocket.recv(n - len(lBuf)))
        return lBuf.getAll()
    
    def _send(data):
        lClientSocket.sendall(data)
    
    lHshP = protocol.ClientHandshakeProtocol(_send, _recv, aClientKey)  # ?
    lServerPKey, lSessionID = lHshP.execute(aServerPKey=aServerPKey, aNickname=aNickname)
    
    lLoop = asyncio.get_event_loop() # ?
    lTransport, lClientGeneralProtocol = lLoop.run_until_complete(lLoop.create_connection(lambda *args, **kwargs: ClientGeneralProtocol(lLoop, lClientKey, lServerPKey, aNickname, lSessionID, *args, **kwargs), sock=lClientSocket))
    try:
        lLoop.run_until_complete(lClientGeneralProtocol.disconnected)
    except KeyboardInterrupt:
        pass
    finally:
        lTransport.close()
        lLoop.close()