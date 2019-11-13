from . import utils
from . import protocol
import time


class Message:
    def __init__(self, aText, aSender, aRecepient, aTimestamp=None):
        self.text = aText
        self.sender = utils.loadRSAKey(aSender, PUB=True)
        self.recepient = utils.loadRSAKey(aRecepient, PUB=True)
        self.timestamp = aTimestamp if aTimestamp is not None else int(time.time())
        self.stripCsi()
    
    @classmethod
    def fromPPacket(cls, ppacket, aSender, aRecepient):
        return cls(ppacket.get_MSG().decode(), aSender, aRecepient, ppacket.get_TIME())
    
    def stripCsi(self):
        self.text = utils.stripCsi(self.text)
    
    # ? def toPPacket(self)
    
    def __str__(self):  # TODO: Temporary
        lSender = self.sender.getReprName()
        lRecepient = self.recepient.getReprName()
        lTime = time.asctime(time.localtime(self.timestamp))
        lText = self.text
        return "[*] Message from: {sender}\nTo: {recepient}\nAt: {time}\n-----\n{text}\n[*]".format(sender=lSender, recepient=lRecepient, time=lTime, text=lText)