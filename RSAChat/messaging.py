import time
from collections import deque
import cmd
from RSAChat import utils
from RSAChat.utils.console import *
from RSAChat import protocol


class Message:
    def __init__(self, aText, aSender, aRecepient, aTimestamp=None):
        assert len(aText) <= 30000
        self.text = aText
        self.sender = utils.RSA.loadKey(aSender, PUB=True)
        self.recepient = utils.RSA.loadKey(aRecepient, PUB=True)
        self.timestamp = aTimestamp if aTimestamp is not None else int(time.time())
        self.sanitizeCsi()
    
    @classmethod
    def fromPPacket(cls, ppacket, aSender, aRecepient):
        return cls(ppacket.get_MSG().decode(), aSender, aRecepient, ppacket.get_TIME())
    
    def toPPacket(self, aSenderKey):
        return protocol.PPACKET.build(self.text, aSenderKey, self.timestamp)
    
    def sanitizeCsi(self):
        self.text = utils.ColorProvider.getInstance().strip(self.text)
    
    def __str__(self):  # TODO: Temporary
        lSender = self.sender.getReprName()
        lRecepient = self.recepient.getReprName()
        lTime = time.asctime(time.localtime(self.timestamp))
        lText = self.text
        return "[*] Message from: {sender}\nTo: {recepient}\nAt: {time}\n-----\n{text}\n-----".format(sender=lSender, recepient=lRecepient, time=lTime, text=lText)


class MessagingConsole(Console):
    name = "msg"
    intro = """#####################\n  Messaging Console  \n#####################"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outgoingQueue = deque()
        self.incomingQueue = deque()
        self.readyToOutput = True
   
    def setIdentity(self, aIdentity):
        aIdentity = utils.RSA.loadKey(aIdentity, PUB=True)
        self.identity = aIdentity
    
    def getIdentity(self):
        return self.identity
    
    def tmp(self, key):
        self.serverPKey = utils.RSA.loadKey(key, PUB=True)
    
    def getOutgoing(self):
        if len(self.outgoingQueue) == 0:
            raise utils.NotEnoughDataException()
        return self.outgoingQueue.popleft()
    
    def addOutgoing(self, msg):
        self.outgoingQueue.append(msg)
    
    def getIncoming(self):
        if len(self.incomingQueue) == 0:
            raise utils.NotEnoughDataException()
        return self.incomingQueue.popleft()
    
    def addIncoming(self, msg):
        self.incomingQueue.append(msg)
    
    def handleIncoming(self):
        while True:
            if not self.readyToOutput:
                continue
            try:
                lMsg = self.getIncoming()
            except utils.NotEnoughDataException:
                continue
            print("\x1b[2K\x1b[1G", end="")
            print(lMsg)
            print(self.prompt, end="")
            utils.flush()
    
    def cmdloop(self, intro=None):
        utils.startThread(self.handleIncoming)
        return super().cmdloop(intro=intro)
    
    @Command.parametric("Compose a message and send it")
    def do_compose(self):  # TODO: use readline and autocompletion
        lTo = input("To: ").strip()
        if lTo in ("*", ""):
            lTo = self.serverPKey  # TODO: Move to an Identity class
        else:
            lTo = utils.RSA.loadKey(lTo, PUB=True)
        lText = input("Body:\n")
        lSend = (input("Send? [Y]/[n]: ") + "y")[0].lower()
        if lSend == "n":
            return
        lMsg = Message(lText, self.identity, lTo)
        self.addOutgoing(lMsg)


def start_console():
    lConsole = MessagingConsole()
    utils.startThread(lConsole.cmdloop)
    return lConsole