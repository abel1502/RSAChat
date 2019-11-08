import socketserver
import asyncio
import hashlib
import time
from . import utils
from . import protocol
from . import RSA
from . import messaging


class BaseBlockingProtocol:
    def __init__(self, sender, receiver):
        self.send = sender
        self.recv = receiver
    
    def execute(self):
        return None


class ServerHandshakeProtocol(BaseBlockingProtocol):
    def __init__(self, sender, receiver, aServerKey):
        super().__init__(sender, receiver)
        self.serverKey = aServerKey
    
    def execute(self):
        lStage1Packet = protocol.EPACKET.receive(self.recv)
        if isinstance(lStage1Packet, protocol.HSH_CL_ASK_PACKET):
            lClientPKey = utils.loadRSAKey(lStage1Packet.CL_PKEY, PUB=True)
            self.send(protocol.HSH_SRV_ANS_PACKET.build(self.serverKey, lClientPKey).encode())
        elif isinstance(lStage1Packet, protocol.HSH_CL_SIMPLE_PACKET):
            lClientPKey = utils.loadRSAKey(lStage1Packet.get_CL_PKEY(self.serverKey), PUB=True)
        else:
            assert False
        
        lChallenge = hashlib.md5(utils.randomBytes(16)).digest()
        self.send(protocol.HSH_VER_ASK_PACKET.build(lChallenge, lClientPKey).encode())
        lStage2Packet = protocol.EPACKET.receive(self.recv)
        if not isinstance(lStage2Packet, protocol.HSH_VER_ANS_PACKET):
            assert False
        if hashlib.sha256(lChallenge).digest() != lStage2Packet.get_SOLUTION(self.serverKey):
            assert False
        return lClientPKey


class ClientHandshakeProtocol(BaseBlockingProtocol):
    def __init__(self, sender, receiver, aClientKey):
        super().__init__(sender, receiver)
        self.clientKey = aClientKey
    
    def execute(self, aServerPKey=None):
        if aServerPKey is None:
            self.send(protocol.HSH_CL_ASK_PACKET.build(self.clientKey).encode())
            lStage1Packet = protocol.EPACKET.receive(self.recv)
            if not isinstance(lStage1Packet, protocol.HSH_SRV_ANS_PACKET):
                assert False
            lServerPKey = utils.loadRSAKey(lStage1Packet.get_S_PKEY(self.clientKey), PUB=True)
        else:
            lServerPKey = aServerPKey
            self.send(protocol.HSH_CL_SIMPLE_PACKET.build(self.clientKey, lServerPKey).encode()))
        
        lStage2Packet = protocol.EPACKET.receive(self.recv)
        if not isinstance(lStage2Packet, protocol.HSH_VER_ASK_PACKET):
            assert False
        lChallenge = lStage2Packet.get_CHALLENGE()
        lSolution = hashlib.sha256(lChallenge).digest()
        self.send(protocol.HSH_VER_ANS_PACKET.build(lSolution, lServerKey).encode())
        return lServerPKey


class ServTCPHandler(socketserver.StreamRequestHandler):
    def __init__(self, aServerKey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serverKey = aServerKey
    
    def recv(self, n):
        lBuf = b''
        while n - len(lBuf) > 0:
            lBuf += self.rfile.read(n - len(lBuf))
        return lBuf
    
    def send(self, data):
        self.wfile.write(data)
    
    def handle(self):
        print("Connection from {0[0]}:{0[1]}".format(self.request.getpeername()))
        # TODO: Timeout and check for shutdown?
        
        self.doHandshake()
        lLoop = asyncio.new_event_loop() # ?
        lTransport, lProtocol = lLoop.run_until_complete(lLoop.connect_accepted_socket(ServLoopHandler, self.request))
        try:
            lLoop.run_forever()
        except KeyboardInterrupt:
            pass
        lLoop.close()
    
    def doHandshake(self):
        lHshP = ServerHandshakeProtocol(self.send, self.recv, self.serverKey)
        self.clientPKey = lHshP.execute()


class ServLoopHandler(asyncio.Protocol):
    def connection_made(self, transport):
        print("General phase")
        self.transport = transport
        self.recvBuf = utils.Buffer()
        self.sendBuf = utils.Buffer()
    
    def _send(self, data):
        self.transport.sendall(data)
    
    def _recv(self, n):
        if len(self.recvBuf) < n:
            assert False
        return self.recvBuf.get(n)
    
    def send(self, data):
        self.sendBuf.put(data)
    
    def flush(self):
        self._send(self.sendBuf.getAll())
    
    def data_received(self, data):
        print('[*]', data)
        self.buf.put(data)
        
    def connection_lost(self, exc=None):
        print("Disconnect")
        # Needed?
        self.transport.close()


def start_server(host="", port=8887, aServerKey=None):
    #utils.checkParamTypes("network.start_server", [host, port, aServerKey], [{str}, {int}, {type(None), str, bytes, RSA.PrivateKey}])
    
    serverKey = utils.loadRSAKey(aServerKey, PRIV=True) if aServerKey is not None else RSA.genKeyPair()[1]
    with socketserver.ThreadingTCPServer(("", 8080), lambda *args, **kwargs: ServTCPHandler(serverKey, *args, **kwargs)) as serv:
        serv.serve_forever()


def connect_client(host, port=8887, aClientKey=None, aServerKey=None):
    #utils.checkParamTypes("network.connect_client", [host, port, aClientKey, aServerKey], [{str}, {int}, {type(None), str, bytes, RSA.PrivateKey}, {type(None), str, bytes, RSA.PublicKey}])    
    clientKey = utils.loadRSAKey(aClientKey, PRIV=True) if aClientKey is not None else RSA.genKeyPair()[1]
    if aServerKey != None:
        pass
    else:
        pass
    