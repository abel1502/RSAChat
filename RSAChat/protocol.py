# TODO: verify tons of stuff!!

import hashlib
import struct
from RSAChat import utils

VERSION = 3
MIN_KEY_LEN = 1023


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
    
    def getId(self):
        return -1
    
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
            elif issubclass(elem[1], PacketData):
                assert elem[2] == 0
                result += self.fields[elem[0]].encode()
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
            elif issubclass(elem[1], PacketData):
                assert elem[2] == 0
                result.fields[elem[0]] = elem[1].receive(receiver, id=result.getId())
            else:
                utils.raiseException("protocol.BasePacket.parse", "Not implemented")
        return result
    
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join(map(lambda x: "{}={}".format(x, repr(self.fields[x])), self.fields)))


class PacketData(BasePacket):
    container = BasePacket
    id = -1
    
    @classmethod
    def receive(cls, receiver, id=None):
        if id is None:
            packet = cls.container.receive(receiver)
            assert cls.id == packet.getId()
            return packet
        if id == cls.id:
            return super().receive(receiver)
        for handler in cls.__subclasses__():
            if handler.id == id:
                return handler.receive(receiver, id=id)
        assert False


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


class EPACKET_TYPE:
    REGULAR = 0
    HSH_CL_ASK = 1
    HSH_SRV_ANS = 2
    HSH_CL_SIMPLE = 3
    HSH_VER_ASK = 4
    HSH_VER_ANS = 5
    HSH_SID = 6


class EPACKET_DATA(PacketData):
    pass


class EPACKET(BasePacket):
    structure = [("EPID", int, 1), ("INNER", EPACKET_DATA, 0)]
    defaultFields = {"EPID": None, "INNER": None}
    
    def getId(self):
        return self.EPID
    
    @classmethod
    def build(cls, inner):
        return cls(EPID=inner.id, INNER=inner)

EPACKET_DATA.container = EPACKET


class HSH_CL_ASK_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_CL_ASK
    structure = [("CL_PKEY", bytes, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @classmethod
    def build(cls, clientPKey):
        clientPKey = utils.RSA.dumpKey(clientPKey, PUB=True).encode()
        return cls(CL_PKEY=clientPKey)
    
    def get_CL_PKEY(self):
        return utils.RSA.loadKey(self.CL_PKEY, PUB=True)


class HSH_SRV_ANS_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_SRV_ANS
    structure = [("S_PKEY", bytes, -2)]
    defaultFields = {"S_PKEY": None}
    
    @classmethod
    def build(cls, serverPKey, clientPKey):
        serverPKey = utils.RSA.dumpKey(serverPKey, PUB=True).encode()
        clientPKey = utils.RSA.loadKey(clientPKey, PUB=True)
        serverPKey = clientPKey.encrypt(serverPKey)
        return cls(S_PKEY=serverPKey)
    
    def get_S_PKEY(self, clientKey):
        clientKey = utils.RSA.loadKey(clientKey, PRIV=True)
        return utils.RSA.loadKey(clientKey.decrypt(self.S_PKEY), PUB=True)


class HSH_CL_SIMPLE_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_CL_SIMPLE
    structure = [("CL_PKEY", bytes, -2)]
    defaultFields = {"CL_PKEY": None}
    
    @classmethod
    def build(cls, clientPKey, serverPKey):
        clientPKey = utils.RSA.dumpKey(clientPKey, PUB=True).encode()
        serverPKey = utils.RSA.loadKey(serverPKey, PRIV=True)
        clientPKey = serverPKey.encrypt(clientPKey)
        return cls(CL_PKEY=clientPKey)
    
    def get_CL_PKEY(self, serverKey):
        serverKey = utils.RSA.loadKey(serverKey, PRIV=True)
        return utils.RSA.loadKey(serverKey.decrypt(self.CL_PKEY), PUB=True)


class HSH_VER_ASK_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_VER_ASK
    structure = [("CHALLENGE", bytes, -2)]
    defaultFields = {"CHALLENGE": None}
    
    @classmethod
    def build(cls, challenge, clientPKey):
        clientPKey = utils.RSA.loadKey(clientPKey, PUB=True)
        challenge = clientPKey.encrypt(challenge)
        return cls(CHALLENGE=challenge)
    
    def get_CHALLENGE(self, clientKey):
        clientKey = utils.RSA.loadKey(clientKey, PRIV=True)
        return clientKey.decrypt(self.CHALLENGE)


class HSH_VER_ANS_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_VER_ANS
    structure = [("SOLUTION", bytes, -2)]
    defaultFields = {"SOLUTION": None}
    
    @classmethod
    def build(cls, solution, serverPKey):
        serverPKey = utils.RSA.loadKey(serverPKey, PUB=True)
        solution = serverPKey.encrypt(solution)
        return cls(SOLUTION=solution)
    
    def get_SOLUTION(self, serverKey):
        serverKey = utils.RSA.loadKey(serverKey, PRIV=True)
        return serverKey.decrypt(self.SOLUTION)


class HSH_SID_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.HSH_SID
    structure = [("SID", bytes, -3)]
    defaultFields = {"SID": None}
    
    @classmethod
    def build(cls, sessionID, otherPKey):
        otherPKey = utils.RSA.loadKey(otherPKey, PUB=True)
        return cls(SID=otherPKey.encrypt(sessionID))
    
    def get_SID(self, selfKey):
        selfKey = utils.RSA.loadKey(selfKey, PRIV=True)
        return selfKey.decrypt(self.SID)


class REGULAR_EPACKET(EPACKET_DATA):
    id = EPACKET_TYPE.REGULAR
    structure = [("EPDATA", bytes, -3)]
    defaultFields = {"EPDATA": None}
    
    @classmethod
    def build(cls, spacket, otherPKey):
        otherPKey = utils.RSA.loadKey(otherPKey, PUB=True)
        return cls(EPDATA=otherPKey.encrypt(spacket.encode()))
    
    def get_EPDATA(self, selfKey):
        selfKey = utils.RSA.loadKey(selfKey, PRIV=True)
        return SPACKET.parse(selfKey.decrypt(self.EPDATA))


class SPACKET_TYPE:
    MESSAGE = 0
    LOOKUP_ASK = 1
    LOOKUP_ANS = 2
    ONLINE_ASK = 3
    ONLINE_ANS = 4


class SPACKET_DATA(PacketData):
    pass


class SPACKET(BasePacket):
    structure = [("SPID", int, 1), ("INNER", SPACKET_DATA, 0), ("SPSID", bytes, 16), ("salt", bytes, 16)]
    defaultFields = {"SPID": None, "INNER": None, "SPSID": None, "salt": None}
    
    def getId(self):
        return self.SPID
    
    def verifySession(self, sessionId):
        return self.SPSID == sessionId
    
    @classmethod
    def build(cls, inner, sessionId):
        return cls(SPID=inner.id, INNER=inner, SPSID=sessionId, salt=hashlib.md5(utils.randomBytes(16)).digest())

SPACKET_DATA.container = SPACKET


class MESSAGE_SPACKET(SPACKET_DATA):
    id = SPACKET_TYPE.MESSAGE
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2)]
    defaultFields = {"SPDATA": None, "SPKEY": None}
    
    @classmethod
    def build(cls, ppacket, recepientPKey):
        recepientPKey = utils.RSA.loadKey(recepientPKey, PUB=True)
        return cls(SPDATA=recepientPKey.encrypt(ppacket.encode()), SPKEY=utils.RSA.dumpKey(recepientPKey, PUB=True).encode())
    
    def get_SPDATA(self, selfKey):
        selfKey = utils.RSA.loadKey(selfKey, PRIV=True)
        return PPACKET.parse(selfKey.decrypt(self.SPDATA))
    
    def get_SPKEY(self):
        return utils.RSA.loadKey(self.SPKEY, PUB=True)


class LOOKUP_ASK_SPACKET(SPACKET_DATA):
    id = SPACKET_TYPE.LOOKUP_ASK
    structure = [("SPRID", int, 2), ("SPTARGET", bytes, -2)]
    defaultFields = {"SPRID": None, "SPTARGET": None}
    
    @classmethod
    def build(cls, rid, target):
        if isinstance(target, str):
            target = target.encode()
        return cls(SPRID=rid, SPTARGET=target)
    
    def get_SPTARGET(self):
        return self.SPTARGET.decode()


class LOOKUP_ANS_SPACKET(SPACKET_DATA):
    id = SPACKET_TYPE.LOOKUP_ANS
    structure = [("SPRID", int, 2), ("SPKEY", bytes, -2)]
    defaultFields = {"SPRID": None, "SPKEY": None}
    
    @classmethod
    def build(cls, rid, pKey):
        if pKey is not None:
            pKey = utils.RSA.dumpKey(pKey, PUB=True).encode()
        else:
            pKey = b""
        return cls(SPRID=rid, SPKEY=pKey)
    
    def get_SPKEY(self):
        if self.SPKEY != b"":
            return utils.RSA.loadKey(self.SPKEY, PUB=True)
        else:
            return None


class ONLINE_ASK_SPACKET(SPACKET_DATA):
    id = SPACKET_TYPE.ONLINE_ASK
    structure = [("SPRID", int, 2)]
    defaultFields = {"SPRID": None}
    
    @classmethod
    def build(cls, rid):
        return cls(SPRID=rid)


class ONLINE_ANS_SPACKET(SPACKET_DATA):
    id = SPACKET_TYPE.ONLINE_ANS
    structure = [("SPRID", int, 2), ("SPONLINE", bytes, -2)]
    defaultFields = {"SPRID": None, "SPONLINE": None}
    
    @classmethod
    def build(cls, rid, online):
        return cls(SPRID=rid, SPONLINE='\n'.join(online).encode())
    
    def get_SPONLINE(self):
        res = self.SPONLINE.decode()
        if res == "":
            return []
        return res.split("\n")


class PPACKET(BasePacket):
    structure = [("salt", bytes, 16), ("MSG", bytes, -2), ("TIME", int, 4), ("HASH", bytes, -2)]
    defaultFields = {"salt": None, "MSG": None, "TIME": None, "HASH":None}
    
    @classmethod
    def build(cls, msg, senderKey, time):
        if isinstance(msg, str):
            msg = msg.encode()
        senderKey = utils.RSA.loadKey(senderKey, PRIV=True)
        replyTo = senderKey.getPublicKey()
        # ? Supporsedly unnecessary
        #MSG = utils.RSA.dumpKey(replyTo, PUB=True).encode() + b'\n' + msg
        MSG = msg
        salt = hashlib.md5(utils.randomBytes(16)).digest()
        TIME = time
        HASH = senderKey.sign(salt + MSG + TIME.to_bytes(4, "big"))
        return cls(MSG=MSG, salt=salt, TIME=TIME, HASH=HASH)
    
    def verify(self, replyTo):
        assert self.isComplete()
        replyTo = utils.RSA.loadKey(replyTo, PUB=True)
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
        lCurPacket = EPACKET.receive(self.recv).INNER
        if isinstance(lCurPacket, HSH_CL_ASK_EPACKET):
            lClientPKey = lCurPacket.get_CL_PKEY()
            self.send(EPACKET.build(HSH_SRV_ANS_EPACKET.build(self.serverKey.getPublicKey(), lClientPKey)).encode())
        elif isinstance(lCurPacket, HSH_CL_SIMPLE_EPACKET):
            lClientPKey = lCurPacket.get_CL_PKEY(self.serverKey)
        else:
            assert False
        
        lChallenge = hashlib.md5(utils.randomBytes(16)).digest()
        self.send(EPACKET.build(HSH_VER_ASK_EPACKET.build(lChallenge, lClientPKey)).encode())
        lCurPacket = HSH_VER_ANS_EPACKET.receive(self.recv).INNER
        if hashlib.sha256(lChallenge).digest() != lCurPacket.get_SOLUTION(self.serverKey):
            assert False
        assert lClientPKey.fields["n"] >= (1 << MIN_KEY_LEN)
        
        lSessionID = hashlib.md5(utils.randomBytes(16)).digest()
        self.send(EPACKET.build(HSH_SID_EPACKET.build(lSessionID, lClientPKey)).encode())
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
            self.send(EPACKET.build(HSH_CL_ASK_EPACKET.build(self.clientKey.getPublicKey())).encode())
            lStage1Packet = HSH_SRV_ANS_EPACKET.receive(self.recv).INNER
            lServerPKey = lStage1Packet.get_S_PKEY(self.clientKey)
        else:
            lServerPKey = utils.RSA.loadKey(aServerPKey, PUB=True)
            self.send(EPACKET.build(HSH_CL_SIMPLE_EPACKET.build(self.clientKey.getPublicKey(), lServerPKey)).encode())
        
        lStage2Packet = HSH_VER_ASK_EPACKET.receive(self.recv).INNER
        lChallenge = lStage2Packet.get_CHALLENGE(self.clientKey)
        lSolution = hashlib.sha256(lChallenge).digest()
        self.send(EPACKET.build(HSH_VER_ANS_EPACKET.build(lSolution, lServerPKey)).encode())
        assert lServerPKey.fields["n"] >= (1 << MIN_KEY_LEN)
        
        lCurPacket = HSH_SID_EPACKET.receive(self.recv).INNER
        lSessionID = lCurPacket.get_SID(self.clientKey)
        return lServerPKey, lSessionID