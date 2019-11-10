import socket
import socketserver
import asyncio
import hashlib
import time
from . import utils
from . import protocol
from . import RSA
from . import messaging


class ServTCPHandler(socketserver.StreamRequestHandler):
    def __init__(self, aServerKey, *args, **kwargs):
        self.serverKey = aServerKey
        super().__init__(*args, **kwargs)
    
    def recv(self, n):
        lBuf = utils.Buffer()
        while n - len(lBuf) > 0:
            lBuf.put(self.rfile.read(n - len(lBuf)))
        return lBuf.getAll()
    
    def send(self, data):
        self.wfile.write(data)
    
    def handle(self):
        utils.log("Connection from {0[0]}:{0[1]}".format(self.request.getpeername()))
        # TODO: Timeout and check for shutdown?
        
        lClientPKey = self.doHandshake()
        lLoop = asyncio.new_event_loop() # ?
        lTransport, lProtocol = lLoop.run_until_complete(lLoop.connect_accepted_socket(lambda *args, **kwargs: ServLoopHandler(self.serverKey, lClientPKey, *args, **kwargs), self.request))
        try:
            lLoop.run_forever()
        except KeyboardInterrupt:
            pass
        lLoop.close()
    
    def doHandshake(self):
        lHshP = protocol.ServerHandshakeProtocol(self.send, self.recv, self.serverKey)
        return lHshP.execute()


class ServLoopHandler(asyncio.Protocol):
    def __init__(self, aServerKey, aClientPKey, *args, **kwargs):
        self.serverKey = aServerKey
        self.clientPKey = aClientPKey
        super().__init__(*args, **kwargs)
    
    def connection_made(self, transport):
        utils.log("General phase")
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
        utils.log('[*]', data)
        self.buf.put(data)
        
    def connection_lost(self, exc=None):
        utils.log("Disconnect")
        # Needed?
        self.transport.close()


class ClientLoopHandler(asyncio.Protocol):
    def __init__(self, aClientKey, aServerPKey, *args, **kwargs):
        self.clientKey = aClientKey
        self.serverPKey = aServerPKey
        super().__init__(*args, **kwargs)
    
    def connection_made(self, transport):
        utils.log("Connected to {0[0]}:{0[1]}".format(transport._sock.getpeername()))
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
        utils.log('[*]', data)
        self.buf.put(data)
        
    def connection_lost(self, exc=None):
        utils.log("Disconnect")
        # Needed?
        self.transport.close()


def start_server(host="", port=8887, aServerKey=None):
    serverKey = utils.loadRSAKey(aServerKey, PRIV=True) if aServerKey is not None else RSA.genKeyPair()[1]
    with socketserver.ThreadingTCPServer((host, port), (lambda *args, **kwargs: ServTCPHandler(serverKey, *args, **kwargs))) as serv:
        serv.serve_forever()


def connect_client(host, port=8887, aClientKey=None, aServerPKey=None):    
    lClientKey = utils.loadRSAKey(aClientKey, PRIV=True) if aClientKey is not None else RSA.genKeyPair()[1]
    lClientSocket = socket.create_connection((host, port))
    
    def _recv(n):
        lBuf = utils.Buffer()
        while n - len(lBuf) > 0:
            lBuf.put(lClientSocket.recv(n - len(lBuf)))
        return lBuf.getAll()
    
    def _send(data):
        lClientSocket.sendall(data)
    
    lHshP = protocol.ClientHandshakeProtocol(_send, _recv, aClientKey)  # ?
    lServerPKey = lHshP.execute(aServerPKey)
    
    lLoop = asyncio.get_event_loop() # ?
    lTransport, lProtocol = lLoop.run_until_complete(lLoop.create_connection(lambda *args, **kwargs: ClientLoopHandler(lClientKey, lServerPKey, *args, **kwargs), sock=lClientSocket))
    try:
        lLoop.run_forever()
    except KeyboardInterrupt:
        pass
    lLoop.close()