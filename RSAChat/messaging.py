from . import utils
from . import protocol
import time


class Message:
    def __init__(self, aText, aSender, aRecepient, aTimestamp=None):
        self.text = aText
        self.sender = utils.loadRSAKey(aSender, PUB=True)
        self.recepient = utils.loadRSAKey(aRecepient, PUB=True)
        self.timestamp = aTimestamp if aTimestamp is not None else int(time.time())
    
    @classmethod
    def fromPPacket(cls, ppacket, aSender, aRecepient):
        return cls(ppacket.get_MSG(), aSender, aRecepient, ppacket.get_TIME())
    
    # ? def toPPacket(self)
    
    def __str__(self):  # TODO: Temporary
        return "[*] Message from:\n{sender}\nto:\n{recepient}\n{time}\n-----\n{text}\n[*]".format(sender=self.sender,
                    recepient=self.recepient, time=time.asctime(time.gmtime(self.timestamp)), text=self.text)