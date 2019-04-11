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
        return self.EPID.to_bytes(1, "big") + self.EPLEN.to_bytes(2, "big") + self.EPDATA
    def extractSPACKET(self, key):
        assert self.isComplete()
        return SPACKET.parse(key.decrypt(self.EPDATA))


class SPACKET:
    def __init__(self, SPDATA, SPKEY):
        self.SPDATA = SPDATA
        self.SPKEY = SPKEY
        self.setLen()
    
    def setLen(self):
        self.SPLEN = len(SPDATA)
        self.SPKEYLEN = len(SPKEY)
    
    def isComplete(self):
        return self.SPDATA is not None and self.SPKEY is not None
    
    @staticmethod
    def parse(data):
        # TODO: FINISH
        SPLEN = int.from_bytes(data[:2], "big")
        data = data[2:]
        assert len(data) - 2 < SPLEN
        SPDATA = data[:SPLEN]
        data = data[SPLEN:]
        SPLEN = int.from_bytes(data[:2], "big")
        data = data[2:]
        assert len(data) - 2 < SPLEN
        SPDATA = data[:SPLEN]
        data = data[SPLEN:]
            



