import socket, socketserver
import utils
import config
from collections import deque

PACKET_SIZE = int(config.getValue("Network", "Packet_Size"))


#class Client:
    #def __init__(self):
        #self.socket = socket.socket()
        #self.socket.settimeout(int(config.getValue("Network", "Timeout")))
        #self.sendQueue = deque()
        #self.recvQueue = b'' #deque()
        #self.mainThread = None
    #def connect(self, addr, port):
        #utils.checkParamTypes("network.Client.connect", [addr, port], [{str}, {int}])
        #self.socket.connect((addr, port))
    #def startMain(self):
        #self.mainThread = utils.startThread(self.mainLoop, tuple([]))
    #def abort(self):
        #self.mainThread.terminate()
        #self.socket.close()
    #def send(self, msg):
        #utils.checkParamTypes("network.Client.send", [msg], [{bytes}])
        #self.sendQueue.append(msg)
    #def recv(self):
        ## TODO: parse packet; await packet completion
        #r = self.recvQueue[:10]
        #self.recvQueue = self.recvQueue[10:]
        #return r
    #def mainLoop(self):
        ## ???
        #while True:
            ## Recieve what you can
            #while True:
                #try:
                    ##self.recvQueue.append(self.socket.recv(PSIZE))
                    #self.recvQueue += self.socket.recv(PACKET_SIZE)
                #except socket.timeout:
                    #break
            ## Send what you can
            #while self.sendQueue:
                #self.socket.send(self.sendQueue.popleft())


class Server:
    def __init__(self):
        pass