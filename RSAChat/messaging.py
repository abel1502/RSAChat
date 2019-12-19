import time
from collections import deque
import re
from RSAChat import utils
from RSAChat.utils.console import *
from RSAChat import protocol


class Message:
    def __init__(self, aText, aSender=None, aRecepient=None, aTimestamp=None):
        assert len(aText) <= 30000
        self.text = aText
        self.sender = utils.RSA.loadKey(aSender, PUB=True) if aSender is not None else None
        self.recepient = utils.RSA.loadKey(aRecepient, PUB=True) if aRecepient is not None else None
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
        lSender = self.sender.getReprName() if self.sender is not None else "-"
        lRecepient = self.recepient.getReprName() if self.recepient is not None else "-"
        lTime = time.asctime(time.localtime(self.timestamp))
        lText = self.text
        return "[*] Message from: {sender}\nTo: {recepient}\nAt: {time}\n-----\n{text}\n-----".format(sender=lSender, recepient=lRecepient, time=lTime, text=lText)


class MessagingConsole(Console):
    name = "msg"
    intro = """#####################\n  Messaging Console  \n#####################"""
    
    def __init__(self, networkClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.networkClient = networkClient
        self.incomingQueue = deque()
   
    def setIdentity(self, aIdentity):
        aIdentity = utils.RSA.loadKey(aIdentity, PUB=True)
        self.identity = aIdentity
    
    def getIdentity(self):
        return self.identity
    
    def getIncoming(self):
        return utils.queueGet(self.incomingQueue)
    
    def addIncoming(self, msg):
        #utils.log("[DBG]", msg)
        self.incomingQueue.append(msg)
    
    def handleIncoming(self):
        while True:
            #if self.prompting:
            #    continue
            try:
                lMsg = self.getIncoming()
            except utils.NotEnoughDataException:
                continue
           #print("\x1b[2K\x1b[1G", end="")
            print(lMsg)
            #print(self.prompt, end="")
            utils.flush()
    
    def cmdloop(self, intro=None):
        utils.startThread(self.handleIncoming)
        return super().cmdloop(intro=intro)
    
    @Command.parametric("Compose a message and send it")
    def do_compose(self):  # TODO: use readline and autocompletion
        lTo = input("To: ").strip()
        if lTo in ("*", ""):
            lTo = None
        elif re.fullmatch(utils.RSA.nicknamePattern, lTo):
            lTo = utils.RSA.loadKey(self.networkClient.sendLookup(lTo), PUB=True)
        else:
            lTo = utils.RSA.loadKey(lTo, PUB=True)
        lText = input("Body:\n")
        lSend = (input("Send? [Y]/[n]: ") + "y")[0].lower()
        if lSend == "n":
            return
        lMsg = Message(lText, self.identity, lTo)
        self.networkClient.sendMessage(lMsg)
    
    @Command.parametric("Get a list of nickname-wielding users online")
    def do_online(self):
        online = self.networkClient.sendOnline()
        self.log(online)
    
    @Command.parametric("Find the publick key for the given nickname")
    def do_lookup(self, nickname):
        key = self.networkClient.sendLookup(nickname)
        self.log(key)


def start_console(networkClient):
    lConsole = MessagingConsole(networkClient)
    utils.startThread(lConsole.cmdloop)
    return lConsole