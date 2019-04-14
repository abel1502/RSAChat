from . import utils
from enum import Enum
import struct


class EPACKET_TYPE(Enum):
    HSH_CL_ASK = 1
    HSH_SRV_ANS = 2
    HSH_CL_SIMPLE = 3
    HSH_VER_ASK = 4
    HSH_VER_ANS = 5
    NORM_PLAIN = 6 # Why the hell?
    NORM_RSA = 7


class EPACKET:
    def __init__(self, EPID=None, EPLEN=None, EPDATA=b''):
        self.EPID = EPID
        self.EPLEN = EPLEN
        self.EPDATA = EPDATA
        if self.EPLEN is not None:
            self.setEPLEN()
    def setEPLEN(self):
        self.EPLEN = len(self.EPDATA)
    def parse(self, data):
        if self.EPID is None and len(data) >= 1:
            data, tmp = utils.popBuf(data, 1)
            self.EPID = int.from_bytes(tmp, "big")
        if self.EPID is not None:
            if self.EPLEN is None and len(data) >= 3:
                data, tmp = utils.popBuf(data, 3)
                self.EPLEN = int.from_bytes(tmp, "big")
            if self.EPLEN is not None:
                if len(self.EPDATA) < self.EPLEN:
                    data, tmp = utils.popBuf(data, self.EPLEN - len(self.EPDATA))
                    self.EPDATA += tmp
                if len(self.EPDATA) == self.EPLEN:
                    return data, True
        return data, False
    def isComplete(self):
        return self.EPID is not None and self.EPLEN is not None and len(self.EPDATA) == self.EPLEN
    def encode(self):
        assert self.isComplete()
        return self.EPID.to_bytes(1, "big") + self.EPLEN.to_bytes(3, "big") + self.EPDATA
    def extractSPACKET(self, key):
        assert self.isComplete()
        return SPACKET.parse(key.decrypt(self.EPDATA))


#class SPACKET:
    #def __init__(self, SPDATA, SPKEY):
        #self.SPDATA = SPDATA
        #self.SPKEY = SPKEY
        #self.setLen()
    
    #def setLen(self):
        #self.SPLEN = len(SPDATA)
        #self.SPKEYLEN = len(SPKEY)
    
    #def isComplete(self):
        #return self.SPDATA is not None and self.SPKEY is not None
    
    #@staticmethod
    #def parse(data):
        ## TODO: FINISH
        #SPLEN = int.from_bytes(data[:2], "big")
        #data = data[2:]
        #assert len(data) - 2 >= SPLEN
        #SPDATA = data[:SPLEN]
        #data = data[SPLEN:]
        #SPKEYLEN = int.from_bytes(data[:2], "big")
        #data = data[2:]
        #assert len(data) == SPKEYLEN
        #SPKEY = data
        #return SPACKET(SPDATA, SPKEY)

    #def encode(self):
        #return self.SPLEN.to_bytes(2, "big") + self.SPDATA + self.SPKEYLEN.to_bytes(2, "big") + self.SPKEY + utils.randomBytes(16)
            



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


class _EPACKET(BasePacket):
    structure = [("EPID", int, 1), ("EPDATA", bytes, -3)]
    fields = {"EPID": None, "EPDATA": None}


class SPACKET(BasePacket):
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2), ("salt", bytes, 16)]
    fields = {"SPDATA": None, "SPKEY": None, "salt":None}

