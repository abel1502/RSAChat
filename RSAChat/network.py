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

def start_server(host="", port=8887, privKey=None):
    utils.checkParamTypes("network.start_server", [host, port, privKey], [{str}, {int}, {type(None), str, bytes, RSA.PrivateKey}])
    privKey = RSA.loadKey(privKey) if privKey is not None else RSA.genKeyPair()[1]
    assert isinstance(privKey, RSA.PrivateKey)
    connections = dict()
    loop = asyncio.get_event_loop()
    coro = loop.create_server(ServerProtocol(privKey, connections), host, port)
    server = loop.run_until_complete(coro)
    print('Serving on {}:{}'.format(*server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


class ServerProtocol(asyncio.Protocol):
    def __init__(self, privKey, connections):
        self.privKey = privKey
        self.connections = connections
    def connection_made(self, transport):
        print("Someone connected")
        self.transport = transport
        self.recvBuf = b''
        self.clPublicKey = None
        self.clPublicKeyVerified = False
        self.processing = False
    def sendPacket(self, packet):
        utils.checkParamTypes("network.ServerProtocol.sendPacket", [packet], [{protocol.EPACKET}])
        print("[S SENDING]", packet)
        self.transport.write(packet.encode())
    def handleSinglePacket(self, packet):
        print("[S RECEIVED]", packet)
        if self.clPublicKey is None:
            if packet.EPID == protocol.EPACKET_TYPE.HSH_CL_ASK:
                # TODO: Verify
                self.clPublicKey = RSA.PublicKey.load(packet.EPDATA.decode())
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_SRV_ANS, EPDATA=self.clPublicKey.encrypt(self.privKey.getPublicKey().dump())))
                self.challenge = hashlib.md5(utils.randomBytes(16)).digest()
                self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_VER_ASK, EPDATA=self.clPublicKey.encrypt(self.challenge)))                
            elif packet.EPID == protocol.EPACKET_TYPE.HSH_CL_SIMPLE:
                # TODO: Verify again
                self.clPublicKey = RSA.PublicKey.load(self.privKey.decrypt(packet.EPDATA).decode())
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
                    self.connections[self.clPublicKey.dump()] = deque()
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
        self.connections[key.dump()].append(packet)
    def data_received(self, data):
        print('[*]', data)
        while self.processing:
            pass
        self.processing = True
        self.recvBuf += data
        result = protocol.EPACKET.parse(self.recvBuf)
        while result is not None:
            self.recvBuf = self.recvBuf[result[0]:]
            self.handleSinglePacket(result[1])
            result = protocol.EPACKET.parse(self.recvBuf)
        #self.processing = False
    def connection_lost(self, exc=None):
        print("[S] Disconnect")
        if self.clPublicKeyVerified:
            self.connections.pop(self.clPublicKey.dump())
        self.transport.close()


#def connect_client(host, port=8887, privKey=None, sKey=None):
    #utils.checkParamTypes("network.connect_client", [host, port, privKey, sKey], [{str}, {int}, {type(None), str, bytes, RSA.PrivateKey}, {type(None), str, bytes, RSA.PublicKey}])    
    #privKey = RSA.loadKey(privKey) if privKey is not None else RSA.genKeyPair()[1]
    #assert isinstance(privKey, RSA.PrivateKey)
    #if sKey != None:
        #sKey = RSA.loadKey(sKey)
        #assert isinstance(sKey, RSA.PublicKey)
    #loop = asyncio.get_event_loop()
    #UserClient = ClientProtocol(privKey, sKey)
    #coro = loop.create_connection(lambda: UserClient, host, port)
    #client = loop.run_until_complete(coro)
    #try:
        #loop.run_forever()
    #except KeyboardInterrupt:
        #pass
    #client.close()
    #loop.run_until_complete(client.wait_closed())    
    #loop.close()


#class ClientProtocol(asyncio.Protocol):
    #def __init__(self, privKey, sKey):
        #self.privKey = privKey
        #self.sPublicKey = sKey
    #def connection_made(self, transport):
        #self.transport = transport
        #self.recvBuf = b''
        #self.verified = False
        #self.initialize()
        #self.processing = False
    #def sendMsg(self, msg, to): # TODO: timestamp?
        #utils.checkParamTypes("network.ClientProtocol.sendMsg", [msg, to], [{str, bytes}, {bytes, str, RSA.PublicKey}])
        #if isinstance(msg, bytes):
            #msg = msg.decode()
        #tmp1 = protocol.PPACKET.build(msg, self.privKey)
        #tmp2 = protocol.SPACKET.build(tmp1, to)
        #tmp3 = protocol.EPACKET.build(tmp2, self.sPublicKey)
        #self.sendPacket(tmp3)
    #def sendPacket(self, packet):
        #utils.checkParamTypes("network.ClientProtocol.sendPacket", [packet], [{protocol.EPACKET}])
        #print("[CL SENDING]", packet)
        #self.transport.write(packet.encode())
    #def initialize(self):
        #if self.sPublicKey is None:
            #self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_CL_ASK, EPDATA=self.privKey.getPublicKey().dump().encode()))
        #else:
            #self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_CL_SIMPLE, EPDATA=self.sPublicKey.encrypt(self.privKey.getPublicKey().dump())))
    #def handleSinglePacket(self, packet):
        #print("[CL RECEIVED]", packet)
        #if self.sPublicKey is None:
            #if packet.EPID == protocol.EPACKET_TYPE.HSH_SRV_ANS:
                ## TODO: Verify
                #self.sPublicKey = RSA.PublicKey.load(self.privKey.decrypt(packet.EPDATA).decode())
            #else:
                ## TODO: Quit this guy!
                #self.connection_lost()
        #elif not self.verified:
            #if packet.EPID == protocol.EPACKET_TYPE.HSH_VER_ASK:
                ## TODO: And again
                #self.sendPacket(protocol.EPACKET(EPID=protocol.EPACKET_TYPE.HSH_VER_ANS, EPDATA=self.sPublicKey.encrypt(hashlib.sha256(self.privKey.decrypt(packet.EPDATA)).digest())))
                #self.verified = True
            #else:
                ## TODO: Quit this guy!
                #self.connection_lost()
        #else:
            ## TODO: Normal packet handling
            #self.handleSPacket(protocol.SPACKET.parse(self.privKey.decrypt(packet.EPDATA)))
    #def handleSPacket(self, packet):
        ## TODO: Implement
        #assert self.privKey.getPublicKey() == RSA.loadKey(packet.SPKEY)
        #self.handlePPacket(protocol.PPACKET.parse(self.privKey.decrypt(packet.SPDATA)))
    #def handlePPacket(self, packet):
        ## TODO: Implement
        #replyTo = packet.MSG.split(b' ', 1)[0]
        #assert packet.verify(replyTo)
        #messaging.INCOMING_QUEUE.append(messaging.Message(packet))
    #def data_received(self, data):
        #while self.processing:
            #pass
        #self.processing = True
        #self.recvBuf += data
        #result = protocol.EPACKET.parse(self.recvBuf)
        #while result is not None:
            #self.recvBuf = self.recvBuf[result[0]:]
            #self.handleSinglePacket(result[1])
            #result = protocol.EPACKET.parse(self.recvBuf)
        #self.processing = False
    #def connection_lost(self, exc=None):
        #print("[C] Disconnect")
        #self.transport.close()


def connect_client(host, port=8887, privKey=None, sKey=None):
    utils.checkParamTypes("network.connect_client", [host, port, privKey, sKey], [{str}, {int}, {type(None), str, bytes, RSA.PrivateKey}, {type(None), str, bytes, RSA.PublicKey}])    
    privKey = RSA.loadKey(privKey) if privKey is not None else RSA.genKeyPair()[1]
    assert isinstance(privKey, RSA.PrivateKey)
    if sKey != None:
        sKey = RSA.loadKey(sKey)
        assert isinstance(sKey, RSA.PublicKey)
    loop = asyncio.get_event_loop()
    UserClient = ClientProtocol(privKey, sKey)
    coro = loop.create_connection(lambda: UserClient, host, port)
    client = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    client.close()
    loop.run_until_complete(client.wait_closed())    
    loop.close()


class ClientProtocol(asyncio.Protocol):
    def __init__(self, privKey, sKey):
        self.privKey = privKey
        self.sPublicKey = sKey
    def connection_made(self, transport):
        self.transport = transport
        self.recvBuf = b''
        self.verified = False
        self.initialize()
        self.processing = False
    def initialize(self):
        self.transport.write(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
    def data_received(self, data):
        while self.processing:
            pass
        self.processing = True
        self.recvBuf += data
        print(data)
        result = protocol.EPACKET.parse(self.recvBuf)
        while result is not None:
            self.recvBuf = self.recvBuf[result[0]:]
            self.handleSinglePacket(result[1])
            result = protocol.EPACKET.parse(self.recvBuf)
        self.processing = False
    def connection_lost(self, exc=None):
        print("[C] Disconnect")
        self.transport.close()
