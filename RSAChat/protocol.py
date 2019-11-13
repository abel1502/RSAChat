# TODO: verify tons of stuff!!

import hashlib
import struct
from . import RSA
from . import utils

VERSION = 2
MIN_KEY_LEN = 1023


class EPACKET_TYPE: # Inheritance from Enum?
    REGULAR = 0
    HSH_CL_ASK = 1
    HSH_SRV_ANS = 2
    HSH_CL_SIMPLE = 3
    HSH_VER_ASK = 4
    HSH_VER_ANS = 5
    HSH_SID = 6


class BasePacket:
    structure = []
    defaultFields = {}
    
    def __init__(self, **kwargs):
        # TODO: Verify types and stuff
        self.fields = {}
        self.fields.update(self.defaultFields)
        for key in self.fields:
            if key in kwargs:
                self.fields[key] = kwargs[key]
        #self.fields.update(kwargs)
    
    def __getattribute__(self, attr):
        if attr == "fields":
            return super().__getattribute__(attr)
        elif attr in self.fields:
            return self.fields[attr]
        elif attr.startswith("get_") and attr[4:] in self.fields:  # ?Set as well
            if attr in dir(self):
                return super().__getattribute__(attr)
            else:
                return lambda: self.fields[attr[4:]]
        else:
            return super().__getattribute__(attr)
    
    def __setattr__(self, attr, val):
        if "fields" in dir(self) and attr in self.fields:
            self.fields[attr] = val
        else:
            super().__setattr__(attr, val)
    
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
            else:
                utils.raiseException("protocol.BasePacket.encode", "Not implemented")
        return result
    
    def copy(self):
        return type(self)(**self.fields)
    
    @classmethod
    def build(cls):
        return cls()
    
    @classmethod
    def parse(cls, buf):
        buf = utils.Buffer(buf)
        return cls.receive(buf.get)
    
    @classmethod
    def receive(cls, receiver):
        # TODO: More verification
        result = cls()
        for elem in cls.structure:
            if elem[1] == int:
                result.fields[elem[0]] = int.from_bytes(receiver(elem[2]), "big")
            elif elem[1] == bytes:
                if elem[2] < 0:
                    length = int.from_bytes(receiver(-elem[2]), "big")
                    result.fields[elem[0]] = receiver(length)
                else:
                    result.fields[elem[0]] = receiver(elem[2])
            else:
                utils.raiseException("protocol.BasePacket.parse", "Not implemented")
        return result
    
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join(map(lambda x: "{}={}".format(x, repr(self.fields[x])), self.fields)))


class EPACKET_DATA(BasePacket):
    id = -1
    
    @classmethod
    def receive(cls, receiver, withID=True):
        if withID:
            assert cls.id == int.from_bytes(receiver(1), "big")
        return super().receive(receiver)
    
    def encode(self, withID=True):
        if withID:
            return self.id.to_bytes(1, "big") + super().encode()
        return super().encode()


class V_INF_PACKET(BasePacket):
    structure = [("VERSION", int, 1)]
    defaultFields = {"VERSION": VERSION}
    
    @classmethod
    def build(cls, overloaded=False):
        if not overloaded:
            return super().build()
        return cls(VERSION=0xff)
    
    def isOverloaded(self):
        return self.VERSION == 0xff


class EPACKET(BasePacket):
    structure = [("EPID", int, 1)]
    defaultFields = {"EPID": None}
    
    @classmethod
    def receive(cls, receiver):
        EPID = super().receive(receiver).EPID
        for lType in EPACKET_DATA.__subclasses__():
            if lType.id == EPID:
                break
        else:
            assert False
        return lType.receive(receiver, withID=False)


class HSH_CL_ASK_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_CL_ASK
    structure = [("CL_PKEY", bytes, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @classmethod
    def build(cls, clientPKey):
        clientPKey = utils.dumpRSAKey(clientPKey, PUB=True).encode()
        return cls(CL_PKEY=clientPKey)
    
    def get_CL_PKEY(self):
        return utils.loadRSAKey(self.CL_PKEY, PUB=True)


class HSH_SRV_ANS_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_SRV_ANS
    structure = [("S_PKEY", bytes, -2)]
    defaultFields = {"S_PKEY": None}
    
    @classmethod
    def build(cls, serverPKey, clientPKey):
        serverPKey = utils.dumpRSAKey(serverPKey, PUB=True).encode()
        clientPKey = utils.loadRSAKey(clientPKey, PUB=True)
        serverPKey = clientPKey.encrypt(serverPKey)
        return cls(S_PKEY=serverPKey)
    
    def get_S_PKEY(self, clientKey):
        clientKey = utils.loadRSAKey(clientKey, PRIV=True)
        return utils.loadRSAKey(clientKey.decrypt(self.S_PKEY), PUB=True)


class HSH_CL_SIMPLE_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_CL_SIMPLE
    structure = [("CL_PKEY", bytes, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @classmethod
    def build(cls, clientPKey, serverPKey):
        clientPKey = utils.dumpRSAKey(clientPKey, PUB=True).encode()
        serverPKey = utils.loadRSAKey(serverPKey, PRIV=True)
        clientPKey = serverPKey.encrypt(clientPKey)
        return cls(CL_PKEY=clientPKey)
    
    def get_CL_PKEY(self, serverKey):
        serverKey = utils.loadRSAKey(serverKey, PRIV=True)
        return utils.loadRSAKey(serverKey.decrypt(self.CL_PKEY), PUB=True)


class HSH_VER_ASK_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_VER_ASK
    structure = [("CHALLENGE", bytes, -2)]
    defaultFields = {"CHALLENGE": None}
    
    @classmethod
    def build(cls, challenge, clientPKey):
        clientPKey = utils.loadRSAKey(clientPKey, PUB=True)
        challenge = clientPKey.encrypt(challenge)
        return cls(CHALLENGE=challenge)
    
    def get_CHALLENGE(self, clientKey):
        clientKey = utils.loadRSAKey(clientKey, PRIV=True)
        return clientKey.decrypt(self.CHALLENGE)


class HSH_VER_ANS_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_VER_ANS
    structure = [("SOLUTION", bytes, -2)]
    defaultFields = {"SOLUTION": None}
    
    @classmethod
    def build(cls, solution, serverPKey):
        serverPKey = utils.loadRSAKey(serverPKey, PUB=True)
        solution = serverPKey.encrypt(solution)
        return cls(SOLUTION=solution)
    
    def get_SOLUTION(self, serverKey):
        serverKey = utils.loadRSAKey(serverKey, PRIV=True)
        return serverKey.decrypt(self.SOLUTION)


class HSH_SID_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_SID
    structure = [("SID", bytes, -3)]
    defaultFields = {"SID": None}
    
    @classmethod
    def build(cls, sessionID, otherPKey):
        otherPKey = utils.loadRSAKey(otherPKey, PUB=True)
        return cls(SID=otherPKey.encrypt(sessionID))
    
    def get_SID(self, selfKey):
        selfKey = utils.loadRSAKey(selfKey, PRIV=True)
        return selfKey.decrypt(self.SID)


# ? Rename all those into ..._EPACKET
class REGULAR_PACKET(EPACKET_DATA):
    id = EPACKET_TYPE.REGULAR
    structure = [("EPDATA", bytes, -3)]
    defaultFields = {"EPDATA": None}
    
    @classmethod
    def build(cls, spacket, otherPKey):
        otherPKey = utils.loadRSAKey(otherPKey, PUB=True)
        return cls(EPDATA=otherPKey.encrypt(spacket.encode()))
    
    def get_EPDATA(self, selfKey):
        selfKey = utils.loadRSAKey(selfKey, PRIV=True)
        return SPACKET.parse(selfKey.decrypt(self.EPDATA))


class SPACKET(BasePacket):
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2), ("SPSID", bytes, 16), ("salt", bytes, 16)]
    defaultFields = {"SPDATA": None, "SPKEY": None, "salt": None, "SPSID": None}
    
    @classmethod
    def build(cls, ppacket, recepientPKey, sessionID):
        recepientPKey = utils.loadRSAKey(recepientPKey, PUB=True)
        return cls(SPDATA=recepientPKey.encrypt(ppacket.encode()), SPKEY=utils.dumpRSAKey(recepientPKey, PUB=True).encode(), SPSID=sessionID, salt=hashlib.md5(utils.randomBytes(16)).digest())
    
    def get_SPDATA(self, selfKey):
        selfKey = utils.loadRSAKey(selfKey, PRIV=True)
        return PPACKET.parse(selfKey.decrypt(self.SPDATA))
    
    def get_SPKEY(self):
        return utils.loadRSAKey(self.SPKEY, PUB=True)


class PPACKET(BasePacket):
    structure = [("salt", bytes, 16), ("MSG", bytes, -2), ("TIME", int, 4), ("HASH", bytes, -2)]
    defaultFields = {"salt": None, "MSG": None, "TIME": None, "HASH":None}
    
    @classmethod
    def build(cls, msg, senderKey, time):
        if isinstance(msg, str):
            msg = msg.encode()
        senderKey = utils.loadRSAKey(senderKey, PRIV=True)
        replyTo = senderKey.getPublicKey()
        # ? Supporsedly unnecessary
        #MSG = utils.dumpRSAKey(replyTo, PUB=True).encode() + b'\n' + msg
        MSG = msg
        salt = hashlib.md5(utils.randomBytes(16)).digest()
        TIME = time
        HASH = senderKey.sign(salt + MSG + TIME.to_bytes(4, "big"))
        return cls(MSG=MSG, salt=salt, TIME=TIME, HASH=HASH)
    
    def verify(self, replyTo):
        assert self.isComplete()
        replyTo = utils.loadRSAKey(replyTo, PUB=True)
        return replyTo.verify(self.salt + self.MSG + self.TIME.to_bytes(4, "big"), self.HASH)


class BaseBlockingProtocol:
    def __init__(self, sender, receiver):
        self.send = sender
        self.recv = receiver
    
    def execute(self):
        return None


class ServerHandshakeProtocol(BaseBlockingProtocol):
    def __init__(self, sender, receiver, aServerKey):
        super().__init__(sender, receiver)
        self.serverKey = aServerKey
    
    def execute(self, overloaded=False):
        if overloaded:
            self.send(V_INF_PACKET.build(overloaded=True).encode())
            assert False
        lCurPacket = V_INF_PACKET.receive(self.recv)
        self.send(V_INF_PACKET.build().encode())
        assert VERSION == lCurPacket.get_VERSION()
        lCurPacket = EPACKET.receive(self.recv)
        if isinstance(lCurPacket, HSH_CL_ASK_PACKET):
            lClientPKey = lCurPacket.get_CL_PKEY()
            self.send(HSH_SRV_ANS_PACKET.build(self.serverKey.getPublicKey(), lClientPKey).encode())
        elif isinstance(lCurPacket, HSH_CL_SIMPLE_PACKET):
            lClientPKey = lCurPacket.get_CL_PKEY(self.serverKey)
        else:
            assert False
        
        lChallenge = hashlib.md5(utils.randomBytes(16)).digest()
        self.send(HSH_VER_ASK_PACKET.build(lChallenge, lClientPKey).encode())
        lCurPacket = HSH_VER_ANS_PACKET.receive(self.recv)
        if hashlib.sha256(lChallenge).digest() != lCurPacket.get_SOLUTION(self.serverKey):
            assert False
        assert lClientPKey.fields["n"] >= 1 << MIN_KEY_LEN
        
        lSessionID = hashlib.md5(utils.randomBytes(16)).digest()  # ? Merge with challenge?
        self.send(HSH_SID_PACKET.build(lSessionID, lClientPKey).encode())
        return lClientPKey, lSessionID


class ClientHandshakeProtocol(BaseBlockingProtocol):
    def __init__(self, sender, receiver, aClientKey):
        super().__init__(sender, receiver)
        self.clientKey = aClientKey
    
    def execute(self, aServerPKey=None):
        self.send(V_INF_PACKET.build().encode())
        lStage0Packet = V_INF_PACKET.receive(self.recv)
        if lStage0Packet.isOverloaded():
            utils.log("Server overloaded")
            assert False
        assert VERSION == lStage0Packet.get_VERSION()
        if aServerPKey is None:
            self.send(HSH_CL_ASK_PACKET.build(self.clientKey.getPublicKey()).encode())
            lStage1Packet = HSH_SRV_ANS_PACKET.receive(self.recv)
            lServerPKey = lStage1Packet.get_S_PKEY(self.clientKey)
        else:
            lServerPKey = utils.loadRSAKey(aServerPKey, PUB=True)
            self.send(HSH_CL_SIMPLE_PACKET.build(self.clientKey.getPublicKey(), lServerPKey).encode())
        
        lStage2Packet = HSH_VER_ASK_PACKET.receive(self.recv)
        lChallenge = lStage2Packet.get_CHALLENGE(self.clientKey)
        lSolution = hashlib.sha256(lChallenge).digest()
        self.send(HSH_VER_ANS_PACKET.build(lSolution, lServerPKey).encode())
        assert lServerPKey.fields["n"] >= 1 << MIN_KEY_LEN
        
        lCurPacket = HSH_SID_PACKET.receive(self.recv)
        lSessionID = lCurPacket.get_SID(self.clientKey)
        return lServerPKey, lSessionID