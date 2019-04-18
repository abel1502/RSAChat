import socket, socketserver
from . import utils
from . import config
from collections import deque
import time
import asyncio
from . import protocol
from . import RSA
from . import cryptoRandom
import hashlib

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
        #self.curPacket = protocol.EPACKET()
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
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print("[*]", packet.EPID, packet.EPDATA)
        global SERVER
        if self.clPublicKey is None:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_CL_ASK:
                # TODO: Verify
                self.clPublicKey = RSA.PublicKey.load(packet.EPDATA.decode())
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_SRV_ANS, EPDATA=self.clPublicKey.encrypt(SERVER.privKey.getPublicKey.dump())))
            elif packet.EPID == protocol.EPACKET_TYPE.HSH_CL_SIMPLE:
                # TODO: Verify again
                self.clPublicKey = RSA.PublicKey.load(SERVER.privKey.decrypt(packet.EPDATA).decode())
                self.challenge = hashlib.md5(utils.randomBytes(16)).digest()
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_VER_ASK, EPDATA=self.clPublicKey.encrypt(self.challenge)))
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        elif not self.clPublicKeyVerified:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_VER_ANS:
                # TODO: And again
                if hashlib.sha256(self.challenge).digest() == SERVER.privKey.decrypt(packet.EPDATA):
                    self.clPublicKeyVerified = True
                else:
                    # TODO: Quit this guy!
                    self.connection_lost()
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        else:
            # TODO: Normal packet handling
            self.handleSPacket(protocol.SPACKET.parse(SERVER.privKey.decrypt(packet.EPDATA)))
    def handleSPacket(self, packet):
        pass
    def data_received(self, data):
        #print('[*]', data)
        self.recvBuf += data
        result = protocol.EPACKET.parse(self.recvBuf)
        while result is not None:
            self.recvBuf = self.recvBuf[result[0]:]
            self.packets.append(result[1])
        #self.recvBuf += data
        #self.recvBuf, success = self.curPacket.parse(self.recvBuf)
        #while success:
            #self.packets.append(self.curPacket)
            #self.curPacket = protocol.EPACKET()
            #self.recvBuf, success = self.curPacket.parse(self.recvBuf)
    def connection_lost(self, exc=None):
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
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print(packet.EPID, packet.EPLEN, packet.EPDATA)
    def data_received(self, data):
        self.recvBuf += data
        result = protocol.EPACKET.parse(self.recvBuf)
        while result is not None:
            self.recvBuf = self.recvBuf[result[0]:]
            self.packets.append(result[1])
    def connection_lost(self, exc=None):
        self.mainThread.stop()
        self.transport.close()
