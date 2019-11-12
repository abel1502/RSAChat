from . import utils
from . import protocol
import time


class Message:
    def __init__(self, aText, aSender, aReceiver, aTimestamp=None):
        self.text = aText
        self.sender = utils.loadRSAKey(aSender, PUB=True)
        self.receiver = utils.loadRSAKey(aReceiver, PUB=True)
        self.timestamp = aTinestamp if aTimestamp is not None else int(time.time())
    
    @classmethod
    def fromPPacket(self, ppacket, aSender, aReceiver):
        return cls(ppacket.get_MSG(), aSender, aReceiver, ppacket.get_TIME)
    
    # ? def toPPacket(self)