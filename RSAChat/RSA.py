from . import utils
from . import math
import base64
import os
from . import config

DEFAULT_E = int(config.getValue("RSA", "Default_E", "65537"))


class PublicKey:
    def __init__(self, n, e):
        utils.checkParamTypes("RSA.PublicKey", (n, e), ({int}, {int}))
        self.n = n
        self.e = e
    
    def encrypt(self, msg):
        #if blockLen is None:
        #    blockLen = int(math.log(self.n, 256))
        utils.checkParamTypes("RSA.PublicKey.encrypt", [msg], [{int, bytes}])
        #blockSize = 256 ** blockLen
        #if blockSize >= self.n:
        #    utils.raiseException("in RSA.PublicKey.encrypt", "Each block must be less than N")
        if type(msg) == bytes:
            msg = int.from_bytes(msg, "big") #msg.to_bytes(math.ceil(math.log(msg, 256)))
        #if len(msg) % blockLen != 0:
        #    msg = bytes([0] * (blockLen - len(msg) % blockLen)) + msg
        encrypted = 0
        #for i in range(0, len(msg), blockLen):
        while msg > 0:
            encrypted = encrypted * self.n + self._encryptBlock(msg % self.n)
            msg //= self.n
        return utils.int2bytes(encrypted)
    
    def _encryptBlock(self, msg):
        utils.checkParamTypes("RSA.PublicKey._encryptBlock", [msg], [{int, bytes}])
        if type(msg) == bytes:
            msg = int.from_bytes(msg, "big")
        if msg >= self.n:
            utils.raiseException("RSA.PublicKey._encryptBlock", "Message must be less than N")
        return pow(msg, self.e, self.n)
    
    def dump(self):
        return("#AbelRSA Public Key#{}#{}#".format(base64.b64encode(utils.int2bytes(self.n)).decode(), base64.b64encode(utils.int2bytes(self.e)).decode()))
    
    def load(keyStr):
        utils.checkParamTypes("RSA.PublicKey.load", [keyStr], [{str}])
        keyStr = keyStr.strip()
        if keyStr.count("#") != 4:
            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")
        keyStr = keyStr.strip('#')
        name, n, e= keyStr.split('#')
        if name != "AbelRSA Public Key":
            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")
        try:
            n = int.from_bytes(base64.b64decode(n.encode()), 'big')
            e = int.from_bytes(base64.b64decode(e.encode()), 'big')
            return PrivateKey(n, e, d)
        except:
            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")


class PrivateKey:
    def __init__(self, n, e, d):
        utils.checkParamTypes("RSA.PrivateKey", (n, e, d), ({int}, {int}, {int}))
        self.n = n
        self.e = e
        self.d = d
    
    def _decryptBlock(self, msg):
        utils.checkParamTypes("RSA.PrivateKey._decryptBlock", [msg], [{int, bytes}])
        if type(msg) == bytes:
            msg = int.from_bytes(msg, "big")
        if msg >= self.n:
            utils.raiseException("RSA.PrivateKey._decryptBlock", "Message must be less than N")
        return pow(msg, self.d, self.n)
    
    def decrypt(self, msg):
        #if blockLen is None:
        #    blockLen = int(math.log(self.n, 256))
        utils.checkParamTypes("RSA.PrivateKey.decrypt", [msg], [{int, bytes}])
        #blockSize = 256 ** blockLen
        #if blockSize >= self.n:
        #    utils.raiseException("RSA.PrivateKey.decrypt", "Each block must be less than N")
        if type(msg) == bytes:
            msg = int.from_bytes(msg, "big") #msg.to_bytes(math.ceil(math.log(msg, 256)), "big")
        #if len(msg) % blockLen != 0:
        #    msg = bytes([0] * (blockLen - len(msg) % blockLen)) + msg
        decrypted = 0
        #for i in range(0, len(msg), blockLen):
        while msg > 0:
            decrypted = decrypted * self.n + self._decryptBlock(msg % self.n)
            msg //= self.n
        return utils.int2bytes(decrypted)
    
    def sign(self, msg):
        utils.checkParamTypes("RSA.PrivateKey.sign", [msg], [{int, bytes}])
        if type(msg) == bytes:
            msg = int.from_bytes(msg, "big")
        if msg >= self.n:
            utils.raiseException("RSA.PrivateKey.sign", "Message must be less than N")
        return pow(msg, self.d, self.n)
    
    def dump(self):
        return("#AbelRSA Private Key#{}#{}#{}#".format(base64.b64encode(utils.int2bytes(self.n)).decode(), base64.b64encode(utils.int2bytes(self.e)).decode(), base64.b64encode(utils.int2bytes(self.d)).decode()))
    
    def load(keyStr):
        utils.checkParamTypes("RSA.PrivateKey.load", [keyStr], [{str}])
        keyStr = keyStr.strip()
        if keyStr.count("#") != 5:
            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
        keyStr = keyStr.strip('#')
        name, n, e, d = keyStr.split('#')
        if name != "AbelRSA Private Key":
            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
        try:
            n = int.from_bytes(base64.b64decode(n.encode()), 'big')
            e = int.from_bytes(base64.b64decode(e.encode()), 'big')
            d = int.from_bytes(base64.b64decode(d.encode()), 'big')
            return PrivateKey(n, e, d)
        except:
            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
    
    def getPublicKey(self):
        return PublicKey(self.n, self.e)


def genKeyPair(length=1024, custom_e=None):
    utils.checkParamTypes("RSA.genKeyPair", [length, custom_e], [{int}, {type(None), int}])
    if custom_e is None:
        e = DEFAULT_E
    else:
        e = custom_e
    p = utils.randomPrime(length // 8, length // 2)
    remLength = length - int(math.log(p, 2))
    q = utils.randomPrime(remLength, remLength + 2)
    n = p * q
    while utils.egcd(n, e)[2] != 1:
        p = utils.randomPrime(length // 8, length // 2)
        remLength = length - math.log(p, 2)
        q = utils.randomPrime(remLength, remLength + 2)
        n = p * q
    phi = (p - 1) * (q - 1)
    d = utils.modularInverse(e, phi)
    return (PublicKey(n, e), PrivateKey(n, e, d))


#def getSessionKey(clientPublicKey, length=256):
    #utils.checkParamTypes("RSA.genSessionKey", [clientPublicKey, length], [{PublicKey}, {int}])
    #plainKey = os.urandom(length)
    #return plainKey, clientPublicKey.encrypt(plainKey)