from . import utils
from enum import Enum
#import struct
import time
from . import RSA
import hashlib


class EPACKET_TYPE(Enum):
    REGULAR = 0
    HSH_CL_ASK = 1
    HSH_SRV_ANS = 2
    HSH_CL_SIMPLE = 3
    HSH_VER_ASK = 4
    HSH_VER_ANS = 5


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
                    value = '\x00' * (elem[2] - len(value)) + value
                    result += value
            else:
                utils.raiseException("protocol.BasePacket.encode", "Not implemented")
        return result
    
    @classmethod
    def parse(cls, buf):
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
            else:
                utils.raiseException("protocol.BasePacket.encode", "Not implemented")
        return ptr, result


class EPACKET(BasePacket):
    structure = [("EPID", int, 1), ("EPDATA", bytes, -3)]
    defaultFields = {"EPID": None, "EPDATA": None}


class SPACKET(BasePacket):
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2), ("salt", bytes, 16)]
    defaultFields = {"SPDATA": None, "SPKEY": None, "salt": None}


class PPACKET(BasePacket):
    structure = [("salt", bytes, 16), ("MSG", bytes, -2), ("TIME", int, 4), ("HASH", bytes, -2)]
    defaultFields = {"salt": None, "MSG": None, "TIME": None, "HASH":None}
    
    @staticmethod
    def build(msg, sendTo, key):
        # TODO: Finish
        utils.checkParamTypes("protocol.PPACKET.build", (msg, sendto, key), ({bytes, str}, {bytes, str, RSA.PublicKey}, {bytes, str, RSA.PrivateKey}))
        if isinstance(msg, str):
            msg = msg.encode()
        
        if isinstance(sendTo, bytes):
            sendTo = sendTo.decode()
        if isinstance(sendTo, str):
            sendTo = RSA.PublicKey.load(sendTo)
        
        if isinstance(key, bytes):
            key = key.decode()
        if isinstance(key, str):
            key = RSA.PrivateKey.load(key)
        
        replyTo = key.getPublicKey()
        
        plain_MSG = replyTo + b'\n' + msg
        MSG = sendTo.encrypt(plainMSG)
        salt = hashlib.md5(utils.randomBytes(16)).digest()
        TIME = int(time.time())
        HASH = key.sign(hashlib.sha256(salt + plainMSG + TIME.to_bytes(4, "big")).digest())
        return PPACKET(MSG=MSG, salt=salt, TIME=TIME, HASH=HASH)
    
    def extractPlain(self, key):
        utils.checkParamTypes("protocol.PPACKET.extractPlain", (key), ({bytes, str, RSA.PrivateKey}))
        if isinstance(key, bytes):
            key = key.decode()
        if isinstance(key, str):
            key = RSA.PublicKey.load(key)
        return key.decrypt(self.MSG).split(b'\n', 1)
    
    def verify(self, key):
        utils.checkParamTypes("protocol.PPACKET.verify", (key), ({bytes, str, RSA.PublicKey}))
        if isinstance(key, bytes):
            key = key.decode()
        if isinstance(key, str):
            key = RSA.PublicKey.load(key)
        return key.verify(self.fields["HASH"]) == hashlib.sha256(self.salt + b'\n'.join(self.extractPlain()) + self.time.to_bytes(4, "big")).digest()


