from . import utils
from enum import Enum
import struct


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
    fields = {"EPID": None, "EPDATA": None}


class SPACKET(BasePacket):
    structure = [("SPDATA", bytes, -2), ("SPKEY", bytes, -2), ("salt", bytes, 16)]
    fields = {"SPDATA": None, "SPKEY": None, "salt":None}


