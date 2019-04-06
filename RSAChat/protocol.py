from . import utils
from enum import Enum
import struct


class EPACKET_TYPE(Enum):
    pass


class EPACKET:
    def __init__(self, EPID=None, EPLEN=None, EPDATA=b''):
        self.EPID = EPID
        self.EPLEN = EPLEN
        self.EPDATA = EPDATA
    def setEPLEN(self):
        self.EPLEN = len(self.EPDATA)
    def parse(self, data):
        if self.EPID is None and len(data) >= 1:
            data, tmp = utils.popBuf(data, 1)
            self.EPID = int.from_bytes(tmp, "big")
        if self.EPID is not None:
            if self.EPLEN is None and len(data) >= 2:
                data, tmp = utils.popBuf(data, 2)
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
