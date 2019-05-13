# TODO: Replace manual code with <packet>.build

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
from . import messaging

PACKET_SIZE = config.get("Network", "Packet_Size", 4096, int)
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
        self.clPublicKey = None
        self.clPublicKeyVerified = False
        global SERVER
        SERVER.clients.append(self)
        self.mainThread = utils.Thread(target=self.handlePackets)
        self.mainThread.start()
    def sendPacket(self, packet):
        # TODO: Temporary?
        utils.checkParamTypes("network.ServerProtocol.sendPacket", [packet], [{protocol.EPACKET}])
        print("[S SENDING]", packet)
        self.transport.write(packet.encode())
    def handlePackets(self):
        global SENDBUF
        while not self.mainThread.stopped():
            if self.clPublicKeyVerified and len(SENDBUF[self.clPublicKey.dump()]) > 0:
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.REGULAR, EPDATA=self.clPublicKey.encrypt(SENDBUF[self.clPublicKey.dump()].popleft())))
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print("[*S]", packet.EPID, packet.EPDATA)
        global SERVER
        if self.clPublicKey is None:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_CL_ASK:
                # TODO: Verify
                self.clPublicKey = RSA.PublicKey.load(packet.EPDATA.decode())
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_SRV_ANS, EPDATA=self.clPublicKey.encrypt(SERVER.privKey.getPublicKey().dump())))
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
                    global SENDBUF
                    SENDBUF[self.clPublicKey.dump()] = deque()
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
        # TODO: !!!!!!!!???? Modify packet
        key = RSA.loadKey(packet.SPKEY)
        assert isinstance(key, RSA.PublicKey)
        print("Gotta send to", key.dump())
        global SENDBUF
        SENDBUF[key] = packet
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
        print("[S] Disconnect")
        self.mainThread.stop()
        self.transport.close()


class Client:
    def __init__(self, host, port=8887, privKey=None, sKey=None):
        global CLIENT
        CLIENT = self
        self.sKey = sKey
        self.privKey = privKey if privKey is not None else RSA.genKeyPair()[1]
        self.eventLoop = asyncio.get_event_loop()
        coro = self.eventLoop.create_connection(ClientProtocol, host, port)
        self.aioClient = self.eventLoop.run_until_complete(coro)
    def sendMsg(self, msg, to):
        self.aioClient[1].sendMsg(msg, to)
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
        global CLIENT
        #CLIENT.protocol = self
        #global CLIENT_PROTOCOL
        #CLIENT_PROTOCOL = self
        self.sPublicKey = CLIENT.sKey
        self.verified = False
        self.initialize()
        self.mainThread = utils.Thread(target=self.handlePackets)
        self.mainThread.start()
    def sendMsg(self, msg, to): # TODO: timestamp?
        utils.checkParamTypes("network.ClientProtocol.sendMsg", [msg, to], [{str, bytes}, {bytes, str, RSA.PublicKey}])
        if isinstance(msg, bytes):
            msg = msg.decode()
        self.sendPacket(protocol.EPACKET.build(protocol.SPACKET.build(protocol.PPACKET.build(msg, CLIENT.privKey), to), self.sPublicKey))
    def sendPacket(self, packet):
        # TODO: Temporary?
        utils.checkParamTypes("network.ClientProtocol.sendPacket", [packet], [{protocol.EPACKET}])
        print("[CL SENDING]", packet)
        self.transport.write(packet.encode())
    def handlePackets(self):
        while not self.mainThread.stopped():
            if len(self.packets) > 0:
                self.handleSinglePacket(self.packets.popleft())
            time.sleep(0.5)
    def initialize(self):
        global CLIENT
        if self.sPublicKey is None:
            self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_CL_ASK, EPDATA=CLIENT.privKey.getPublicKey().dump().encode()))
        else:
            self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_CL_SIMPLE, EPDATA=self.sPublicKey.encrypt(CLIENT.privKey.getPublicKey().dump())))
    def handleSinglePacket(self, packet):
        # TODO: Implement
        print("[CL]", packet.EPID, packet.EPLEN, packet.EPDATA)
        if self.sPublicKey is None:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_SRV_ANS:
                # TODO: Verify
                self.sPublicKey = RSA.PublicKey.load(packet.EPDATA.decode())
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        elif not self.verified:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_VER_ASK:
                # TODO: And again
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_VER_ANS, EPDATA=self.sPublicKey.encrypt(hashlib.sha256(CLIENT.privKey.decrypt(packet.EPDATA)).digest())))
                self.verified = True
            else:
                # TODO: Quit this guy!
                self.connection_lost()
        else:
            # TODO: Normal packet handling
            self.handleSPacket(protocol.SPACKET.parse(CLIENT.privKey.decrypt(packet.EPDATA)))
    def handleSPacket(self, packet):
        # TODO: Implement
        assert CLIENT.privKey.getPublicKey() == RSA.loadKey(packet.SPKEY)
        self.handlePPacket(protocol.PPACKET.parse(CLIENT.privKey.decrypt(packet.SPDATA)))
    def handlePPacket(self, packet):
        # TODO: Implement
        replyTo = packet.MSG.split(b' ', 1)[0]
        assert packet.verify(replyTo)
        messaging.INCOMING_QUEUE.append(messaging.Message(packet))
    def data_received(self, data):
        self.recvBuf += data
        result = protocol.EPACKET.parse(self.recvBuf)
        while result is not None:
            self.recvBuf = self.recvBuf[result[0]:]
            self.packets.append(result[1])
    def connection_lost(self, exc=None):
        print("[C] Disconnect")
        self.mainThread.stop()
        self.transport.close()
