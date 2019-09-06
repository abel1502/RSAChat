# TODO: verify tons of stuff!!!!
# TODO: verify getting the right type of key

from . import utils
from enum import Enum
#import struct
import time
from . import RSA
import hashlib


#class EPACKET_TYPE: # Inheritance from Enum?
    #REGULAR = 0
    #HSH_CL_ASK = 1
    #HSH_SRV_ANS = 2
    #HSH_CL_SIMPLE = 3
    #HSH_VER_ASK = 4
    #HSH_VER_ANS = 5


class BasePacket:
    structure = []
    defaultFields = {}
    
    def __init__(self, **kwargs):
        # TODO: Verify types and stuff
        self.fields = self.defaultFields
        self.fields.update(kwargs)
    
    def __getattribute__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            return self.fields[attr]   
    
    def isComplete(self):
        for field in self.fields:
            if self.fields[field] is None:
                return False
        return True
    
    def encode(self):
        assert self.isComplete()
        result = b''
        for elem in self.structure:
            if elem[1] == int:
                result += self.fields[elem[0]].to_bytes(elem[2], "big")
            elif elem[1] == bytes:
                if elem[2] < 0:
                    result += len(self.fields[elem[0]]).to_bytes(-elem[2], "big") + self.fields[elem[0]]
                else:
                    value = self.fields[elem[0]][-elem[2]:]
                    value = b'\x00' * (elem[2] - len(value)) + value
                    result += value
            elif elem[1] == RSA.PublicKey:
                raw = self.fields[elem[0]].dump().encode()
                if elem[2] < 0:
                    result += len(raw).to_bytes(-elem[2], "big") + raw
                else:
                    value = raw[-elem[2]:]
                    value = b'\x00' * (elem[2] - len(value)) + value
                    result += value
            else:
                utils.raiseException("protocol.BasePacket.encode", "Not implemented")
        return result
    
    @classmethod
    def _parse(cls, buf):
        # TODO: More verification
        result = cls()
        ptr = 0
        for elem in cls.structure:
            if elem[1] == int:
                if ptr + elem[2] > len(buf):
                    return None
                result.fields[elem[0]] = int.from_bytes(buf[ptr:ptr + elem[2]], "big")
                ptr += elem[2]
            elif elem[1] == bytes:
                if elem[2] < 0:
                    if ptr - elem[2] > len(buf):
                        return None
                    length = int.from_bytes(buf[ptr:ptr - elem[2]], "big")
                    ptr += -elem[2]
                    if ptr + length > len(buf):
                        return None                
                    result.fields[elem[0]] = buf[ptr:ptr + length]
                    ptr += length
                else:
                    if ptr + elem[2] > len(buf):
                        return None
                    result.fields[elem[0]] = buf[ptr:ptr + elem[2]]
                    ptr += elem[2]
            elif elem[1] == RSA.PublicKey:
                if elem[2] < 0:
                    if ptr - elem[2] > len(buf):
                        return None
                    length = int.from_bytes(buf[ptr:ptr - elem[2]], "big")
                    ptr += -elem[2]
                    if ptr + length > len(buf):
                        return None                
                    result.fields[elem[0]] = RSA.PublicKey.load(buf[ptr:ptr + length].decode())
                    ptr += length
                else:
                    if ptr + elem[2] > len(buf):
                        return None
                    result.fields[elem[0]] = RSA.PublicKey.load(buf[ptr:ptr + elem[2]].decode())
                    ptr += elem[2]
            else:
                utils.raiseException("protocol.BasePacket._parse", "Not implemented")
        return ptr, result
    
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join(map(lambda x: "{}={}".format(x, repr(self.fields[x])), self.fields)))


class HSH_CL_ASK_PACKET(BasePacket):
    structure = [("CL_PKEY", RSA.PublicKey, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @staticmethod
    def build(clientKey):
        utils.checkParamTypes("protocol.HSH_CL_ASK_PACKET.build", [clientKey], [{bytes, str, RSA.PublicKey}])
        if isinstance(clientKey, RSA.PublicKey):
            clientKey = clientKey.dump().encode()
        elif isinstance(clientKey, str):
            clientKey = clientKey.encode()
        return HSH_CL_ASK_PACKET(CL_PKEY=clientKey)
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class HSH_SRV_ANS_PACKET(BasePacket):
    structure = [("S_PKEY", bytes, -2)]
    defaultFields = {"S_PKEY": None}
    
    @staticmethod
    def build(serverKey, clientKey):
        utils.checkParamTypes("protocol.HSH_SRV_ANS_PACKET.build", [serverKey, clientKey], [{bytes, str, RSA.PublicKey}, {bytes, str, RSA.PublicKey}])
        if isinstance(serverKey, RSA.PublicKey):
            serverKey = serverKey.dump().encode()
        elif isinstance(serverKey, str):
            serverKey = serverKey.encode()
        clientKey = RSA.load(clientKey)
        serverKey = clientKey.encrypt(serverKey)
        return HSH_SRV_ANS_PACKET(S_PKEY=serverKey)
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class HSH_CL_SIMPLE_PACKET(BasePacket):
    structure = [("CL_PKEY", bytes, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @staticmethod
    def build(clientKey, serverKey):
        utils.checkParamTypes("protocol.HSH_CL_SIMPLE_PACKET.build", [clientKey], [{bytes, str, RSA.PublicKey}])
        if isinstance(clientKey, RSA.PublicKey):
            clientKey = clientKey.dump().encode()
        elif isinstance(clientKey, str):
            clientKey = clientKey.encode()
        serverKey = RSA.load(serverKey)
        clientKey = serverKey.encrypt(clientKey)
        return HSH_CL_SIMPLE_PACKET(CL_PKEY=clientKey)
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class HSH_VER_ASK_PACKET(BasePacket):
    structure = [("CHALLENGE", bytes, -2)]
    defaultFields = {"CHALLENGE": None}
    
    @staticmethod
    def build(challenge, clientKey):
        utils.checkParamTypes("protocol.HSH_VER_ASK_PACKET.build", [challenge, clientKey], [{bytes}, {bytes, str, RSA.PublicKey}])
        clientKey = RSA.load(clientKey)
        challenge = clientKey.encrypt(challenge)
        return HSH_VER_ASK_PACKET(CHALLENGE=challenge)
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class HSH_VER_ANS_PACKET(BasePacket):
    structure = [("SOLUTION", bytes, -2)]
    defaultFields = {"SOLUTION": None}
    
    @staticmethod
    def build(solution, serverKey):
        utils.checkParamTypes("protocol.HSH_VER_ANS_PACKET.build", [solution, serverKey], [{bytes}, {bytes, str, RSA.PublicKey}])
        serverKey = RSA.load(serverKey)
        solution = serverKey.encrypt(solution)
        return HSH_VER_ANS_PACKET(SOLUTION=solution)
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class EPACKET(BasePacket):
    structure = [("EPID", int, 1), ("EPDATA", bytes, -3)]
    defaultFields = {"EPID": None, "EPDATA": None}
    
    @staticmethod
    def build(spacket, serverKey):
        utils.checkParamTypes("protocol.EPACKET.build", [spacket, serverKey], [{SPACKET}, {bytes, str, RSA.PublicKey}])
        serverKey = RSA.loadKey(serverKey)
        return EPACKET(EPID=EPACKET_TYPE.REGULAR, EPDATA=serverKey.encrypt(spacket.encode()))
    
    def decrypt(self, key):
        utils.checkParamTypes("protocol.EPACKET.decrypt", [key], [{bytes, str, RSA.PrivateKey}])
        assert self.isComplete()
        assert self.EPID == EPACKET_TYPE.REGULAR
        key = RSA.loadKey(key)
        return SPACKET.parse(key.decrypt(self.EPDATA))
    
    @classmethod
    def parse(cls, buf):
        return cls._parse(buf)


class SPACKET(BasePacket):
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2), ("salt", bytes, 16)]
    defaultFields = {"SPDATA": None, "SPKEY": None, "salt": None}
    
    @staticmethod
    def build(ppacket, sendTo):
        utils.checkParamTypes("protocol.SPACKET.build", [ppacket, sendTo], [{PPACKET}, {bytes, str, RSA.PublicKey}])
        sendTo = RSA.loadKey(sendTo)
        return SPACKET(SPDATA=sendTo.encrypt(ppacket.encode()), SPKEY=sendTo.dump().encode(), salt=hashlib.md5(utils.randomBytes(16)).digest())
    
    def decrypt(self, key):
        utils.checkParamTypes("protocol.SPACKET.decrypt", [key], [{bytes, str, RSA.PrivateKey}])
        assert self.isComplete()
        key = RSA.loadKey(key)
        return PPACKET.parse(key.decrypt(self.SPDATA))[1], RSA.loadKey(self.SPKEY.decode())
    
    @classmethod
    def parse(cls, buf):
        ptr, packet = cls._parse(buf)
        if ptr < len(buf):
            utils.raiseException("protocol.SPACKET.parse", "Buf contains extra information")
        return packet


class PPACKET(BasePacket):
    structure = [("salt", bytes, 16), ("MSG", bytes, -2), ("TIME", int, 4), ("HASH", bytes, -2)]
    defaultFields = {"salt": None, "MSG": None, "TIME": None, "HASH":None}
    
    @staticmethod
    def build(msg, key):
        # TODO: Finish
        utils.checkParamTypes("protocol.PPACKET.build", [msg, key], [{bytes, str}, {bytes, str, RSA.PrivateKey}])
        if isinstance(msg, str):
            msg = msg.encode()
        assert len(msg) < 30000
        key = RSA.loadKey(key)
        replyTo = key.getPublicKey()
        MSG = replyTo.dump().encode() + b'\n' + msg
        salt = hashlib.md5(utils.randomBytes(16)).digest()
        TIME = int(time.time())
        HASH = key.sign(hashlib.sha256(salt + MSG + TIME.to_bytes(4, "big")).digest())
        return PPACKET(MSG=MSG, salt=salt, TIME=TIME, HASH=HASH)
        
    def verify(self, replyTo):
        utils.checkParamTypes("protocol.PPACKET.verify", [replyTo], [{bytes, str, RSA.PublicKey}])
        assert self.isComplete()
        replyTo = RSA.loadKey(replyTo)
        return replyTo.verify(self.HASH) == hashlib.sha256(self.salt + self.MSG + self.TIME.to_bytes(4, "big")).digest()
    
    @classmethod
    def parse(cls, buf):
        ptr, packet = cls._parse(buf)
        if ptr < len(buf):
            utils.raiseException("protocol.PPACKET.parse", "Buf contains extra information")
        return packet    


class ProtocolNode:
    def __init__(self, pType, sendNode=True, children=[], preProcess=(lambda *args: None), postProcess=(lambda *args: None)):
        self.pType = pType
        self.sendNode = sendNode
        self.children = children
        self.nextId = 0
        self.preProcess = preProcess
        self.postProcess = postProcess
    
    def apply(self, networkHandler):
        if self.sendNode:
            packet = self.preProcess(networkHandler)
            networkHandler.send(packet)
            self.postProcess(networkHandler)
        else:
            self.preProcess(networkHandler)
            packet = networkHandler.parseRecv(pType)
            self.postProcess(networkHandler, packet)
    
    def next(self):
        if self.isTerm():
            return None
        return self.children[self.nextId]
    
    def isTerm(self):
        return len(self.children) == 0


class ProtocolHandler:
    def __init__(self, protocolTree):
        self.curNode = protocolTree
        self.networkHandler = None
    
    def wrap(self, networkHandler):
        self.networkHandler = networkHandler
    
    def start(self):
        while self.curNode is not None:
            self.curNode.apply(networkHandler)
            self.curNode = self.curNode.next()