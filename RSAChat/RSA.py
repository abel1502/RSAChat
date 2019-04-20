from . import utils
import math
import base64
import os
from . import config

DEFAULT_E = config.get("Crypto", "Default_E", 65537, int)


class PublicKey:
    def __init__(self, n, e):
        utils.checkParamTypes("RSA.PublicKey", (n, e), ({int}, {int}))
        self.n = n
        self.e = e
        self.blockLen = int(math.log(self.n, 256))  # One of those if FF padding
    
    def encrypt(self, msg):
        utils.checkParamTypes("RSA.PublicKey.encrypt", [msg], [{bytes}])
        padAmount = (-len(msg)) % (self.blockLen - 1)
        #msg = b'\x00' * ((-len(msg)) % (self.blockLen - 1)) + msg  # ?
        encrypted = 1
        for block in range((len(msg) + padAmount) // (self.blockLen - 1)):
            encrypted = encrypted * self.n + self._encryptBlock(msg[max(block * (self.blockLen - 1) - padAmount, 0):(block + 1) * (self.blockLen - 1) - padAmount])
        return utils.int2bytes(encrypted)
    
    def verify(self, msg):
        utils.checkParamTypes("RSA.PublicKey.verify", [msg], [{bytes}])
        return PrivateKey(self.n, -1, self.e).decrypt(msg)
        #msg = int.from_bytes(msg, "big")
        #if msg >= self.n:
            #utils.raiseException("RSA.PublicKey._encryptBlock", "Message must be less than N")
        #return utils.int2bytes(pow(msg, self.e, self.n))[1:]
    
    def _encryptBlock(self, msg):
        utils.checkParamTypes("RSA.PublicKey._encryptBlock", [msg], [{bytes}])
        msg = b"\xff" + msg
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
            return PublicKey(n, e)
        except:
            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")


class PrivateKey:
    def __init__(self, n, e, d):
        utils.checkParamTypes("RSA.PrivateKey", (n, e, d), ({int}, {int}, {int}))
        self.n = n
        self.e = e
        self.d = d
        self.blockLen = int(math.log(self.n, 256))  # One of those if FF padding
    
    def _decryptBlock(self, msg):
        utils.checkParamTypes("RSA.PrivateKey._decryptBlock", [msg], [{bytes}])
        msg = int.from_bytes(msg, "big")
        if msg >= self.n:
            utils.raiseException("RSA.PrivateKey._decryptBlock", "Message must be less than N")
        return utils.int2bytes(pow(msg, self.d, self.n))[1:]
    
    def decrypt(self, msg):
        utils.checkParamTypes("RSA.PrivateKey.decrypt", [msg], [{bytes}])
        msg = int.from_bytes(msg, "big")
        decrypted = b''
        while msg > 0:
            decrypted = self._decryptBlock(utils.int2bytes(msg % self.n)) + decrypted
            msg = msg // self.n
        return decrypted
    
    def sign(self, msg):
        utils.checkParamTypes("RSA.PrivateKey.sign", [msg], [{bytes}])
        return PublicKey(self.n, self.d).encrypt(msg)
        #msg = b"\xff" + msg
        #msg = int.from_bytes(msg, "big")
        #if msg >= self.n:
            #utils.raiseException("RSA.PrivateKey.sign", "Message must be less than N")
        #return utils.int2bytes(pow(msg, self.d, self.n))
    
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


def loadKey(key):
    utils.checkParamTypes("RSA.loadKey", [key], [{bytes, str, PublicKey, PrivateKey}])
    if isinstance(key, bytes):
        key = key.decode()
    if isinstance(key, str):
        try:
            return PrivateKey.load(key)
        except:
            return PublicKey.load(key)
    else:
        return key