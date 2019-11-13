from . import utils
import math
import base64
import os
from enum import Enum
import hashlib
#from . import config

#DEFAULT_E = config.get("Crypto", "Default_E", 65537, int)
DEFAULT_E = 65537


def egcd(a, b):
    # Extended Euclid's algorithm
    if b == 0:
        return (1, 0, a)
    x1, y1, g = egcd(b, a % b)
    return (y1, x1 - (a // b) * y1, g)


def modularInverse(n, p):
    # Modular inverse of n by modulo p
    m, k, g = egcd(n, p)
    if g != 1:
        raise Exception("utils.modularInverse", "GCD(n, p) != 1")
    k = -k
    while m < 0:
        m += p
        k += n
    return m


class KeyType(Enum):
    Pub = 0
    Priv = 1


class Key:
    def __init__(self, n, e, d=None):
        self.fields = {}
        self.fields["n"] = n
        self.fields["e"] = e
        self.type = KeyType.Pub
        if d is not None:
            self.fields["d"] = d
            self.type = KeyType.Priv
        self.blockLen = int(math.log(self.fields["n"], 256))  # One of those if FF padding
    
    def _apply(self, data, exp):
        # Data must be bytes
        data = int.from_bytes(data, "big")
        assert 0 <= data < self.fields["n"]
        return utils.int2bytes(pow(data, self.fields[exp], self.fields["n"]))
    
    def pad(self, data):
        return b"\xff" + data
    
    def unpad(self, data):
        return data[1:]
    
    def encrypt(self, data, exp="e"):
        # Data must be bytes (or bytearray?)... ?
        padAmount = (-len(data)) % (self.blockLen - 1)
        lDataBuf = utils.Buffer(data)
        lFirstBlock = self.pad(lDataBuf.get(self.blockLen - 1 - padAmount))
        lRes = int.from_bytes(self._apply(lFirstBlock, exp), "big")
        while len(lDataBuf) > 0:
            lRes = lRes * self.fields["n"] + int.from_bytes(self._apply(self.pad(lDataBuf.get(self.blockLen - 1)), exp), "big")
        return utils.int2bytes(lRes)
    
    def decrypt(self, data, exp="d"):
        data = int.from_bytes(data, "big")
        lRes = []
        while data > 0:
            lRes.append(self.unpad(self._apply(utils.int2bytes(data % self.fields["n"]), exp)))
            data //= self.fields["n"]
        return b"".join(lRes[::-1])
    
    def sign(self, data, hasher=hashlib.sha256):
        lHash = hasher(data).digest()
        return self.encrypt(lHash, exp="d")
    
    def verify(self, data, signature, hasher=hashlib.sha256):
        lHash = hasher(data).digest()
        lSignedHash = self.decrypt(signature, exp="e")
        return lHash == lSignedHash
    
    @staticmethod
    def load(encKey):
        _dec = lambda val: int.from_bytes(base64.b64decode(val.encode()), "big")
        args = encKey.split("#")
        assert len(args) in (5, 6)
        assert args[0] == args[-1] == ""
        args = args[1:-1]
        if args[0] == "PUB" and len(args) == 3:
            return Key(_dec(args[1]), _dec(args[2]))
        elif args[0] == "PRIV" and len(args) == 4:
            return Key(_dec(args[1]), _dec(args[2]), _dec(args[3]))
        else:
            assert False
    
    def dump(self):
        _enc = lambda val: base64.b64encode(utils.int2bytes(val)).decode()
        if self.type == KeyType.Pub:
            return "#PUB#{n}#{e}#".format(n=_enc(self.fields["n"]), e=_enc(self.fields["e"]))
        else:
            return "#PRIV#{n}#{e}#{d}#".format(n=_enc(self.fields["n"]), e=_enc(self.fields["e"]), d=_enc(self.fields["d"]))
    
    def isPub(self):
        return self.type is KeyType.Pub
    
    def isPriv(self):
        return self.type is KeyType.Priv
    
    def getPublicKey(self):
        assert self.isPriv  # ?
        return Key(self.fields["n"], self.fields["e"])
    
    def getFingerprint(self, hasher=hashlib.sha256, hex=False):
        lHash = hasher(self.dump().encode())
        if hex:
            return lHash.hexdigest()
        return lHash.digest()
    
    def checkFingerprint(self, fingerprint, hasher=hashlib.sha256, hex=False):
        return self.getFingerprint(hasher=hasher, hex=hex) == fingerprint
    
    def getReprName(self, color=True):
        lNickname = utils.generateNickname(self)
        lFingerprint = self.getFingerprint(hex=True)  # ? Is trimming okay?
        return "{}<{}>".format(lNickname, lFingerprint)
    
    def __eq__(self, other):
        return type(self) is type(other) and self.type is other.type and self.fields == other.fields
    
    def __hash__(self):
        return hash(tuple(sorted(self.fields.values())))
    
    def __str__(self):
        return self.dump()
        #if self.isPriv():
        #    return "Key(n={0[n]}, e={0[e]}, d={0[d]})".format(self.fields)
        #else:
        #    return "Key(n={0[n]}, e={0[e]})".format(self.fields)


def genKeyPair(length=1024, custom_e=None):
    if custom_e is None:
        e = DEFAULT_E
    else:
        e = custom_e
    p = utils.randomPrime(length // 8, length // 2)
    remLength = length - int(math.log(p, 2))
    q = utils.randomPrime(remLength, remLength + 2)
    n = p * q
    while egcd(n, e)[2] != 1:
        p = utils.randomPrime(length // 8, length // 2)
        remLength = length - math.log(p, 2)
        q = utils.randomPrime(remLength, remLength + 2)
        n = p * q
    phi = (p - 1) * (q - 1)
    d = modularInverse(e, phi)
    return (Key(n, e), Key(n, e, d))


#class PublicKey:
#    def __init__(self, n, e):
#        utils.checkParamTypes("RSA.PublicKey", (n, e), ({int}, {int}))
#        self.n = n
#        self.e = e
#        self.blockLen = int(math.log(self.n, 256))  # One of those if FF padding
#    
#    def encrypt(self, msg):
#        utils.checkParamTypes("RSA.PublicKey.encrypt", [msg], [{bytes, str}])
#        if isinstance(msg, str):
#            msg = msg.encode()
#        padAmount = (-len(msg)) % (self.blockLen - 1)
#        #msg = b'\x00' * ((-len(msg)) % (self.blockLen - 1)) + msg  # ?
#        encrypted = 1
#        for block in range((len(msg) + padAmount) // (self.blockLen - 1)):
#            encrypted = encrypted * self.n + self._encryptBlock(msg[max(block * (self.blockLen - 1) - padAmount, 0):(block + 1) * (self.blockLen - 1) - padAmount])
#        return utils.int2bytes(encrypted)
#    
#    def verify(self, msg):
#        utils.checkParamTypes("RSA.PublicKey.verify", [msg], [{bytes, str}])
#        if isinstance(msg, str):
#            msg = msg.encode()
#        return PrivateKey(self.n, -1, self.e).decrypt(msg)
#        #msg = int.from_bytes(msg, "big")
#        #if msg >= self.n:
#            #utils.raiseException("RSA.PublicKey._encryptBlock", "Message must be less than N")
#        #return utils.int2bytes(pow(msg, self.e, self.n))[1:]
#    
#    def _encryptBlock(self, msg):
#        utils.checkParamTypes("RSA.PublicKey._encryptBlock", [msg], [{bytes}])
#        msg = b"\xff" + msg
#        msg = int.from_bytes(msg, "big")
#        if msg >= self.n:
#            utils.raiseException("RSA.PublicKey._encryptBlock", "Message must be less than N")
#        return pow(msg, self.e, self.n)
#    
#    def dump(self):
#        return("#AbelRSA Public Key#{}#{}#".format(base64.b64encode(utils.int2bytes(self.n)).decode(), base64.b64encode(utils.int2bytes(self.e)).decode()))
#    
#    def load(keyStr):
#        utils.checkParamTypes("RSA.PublicKey.load", [keyStr], [{str}])
#        keyStr = keyStr.strip()
#        if keyStr.count("#") != 4:
#            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")
#        keyStr = keyStr.strip('#')
#        name, n, e= keyStr.split('#')
#        if name != "AbelRSA Public Key":
#            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")
#        try:
#            n = int.from_bytes(base64.b64decode(n.encode()), 'big')
#            e = int.from_bytes(base64.b64decode(e.encode()), 'big')
#            return PublicKey(n, e)
#        except:
#            utils.raiseException("RSA.PublicKey.load", "keyStr is not a valid AbelRSA Public Key")
#    
#    def __eq__(self, other):
#        if isinstance(other, self.__class__):
#            return self.n == other.n and self.e == other.e
#        else:
#            return False


#class PrivateKey:
#    def __init__(self, n, e, d):
#        utils.checkParamTypes("RSA.PrivateKey", (n, e, d), ({int}, {int}, {int}))
#        self.n = n
#        self.e = e
#        self.d = d
#        self.blockLen = int(math.log(self.n, 256))  # One of those if FF padding
#    
#    def _decryptBlock(self, msg):
#        utils.checkParamTypes("RSA.PrivateKey._decryptBlock", [msg], [{bytes}])
#        msg = int.from_bytes(msg, "big")
#        if msg >= self.n:
#            utils.raiseException("RSA.PrivateKey._decryptBlock", "Message must be less than N")
#        return utils.int2bytes(pow(msg, self.d, self.n))[1:]
#    
#    def decrypt(self, msg):
#        utils.checkParamTypes("RSA.PrivateKey.decrypt", [msg], [{bytes, str}])
#        if isinstance(msg, str):
#            msg = msg.encode()        
#        msg = int.from_bytes(msg, "big")
#        decrypted = b''
#        while msg > 0:
#            decrypted = self._decryptBlock(utils.int2bytes(msg % self.n)) + decrypted
#            msg = msg // self.n
#        return decrypted
#    
#    def sign(self, msg):
#        utils.checkParamTypes("RSA.PrivateKey.sign", [msg], [{bytes, str}])
#        if isinstance(msg, str):
#            msg = msg.encode()        
#        return PublicKey(self.n, self.d).encrypt(msg)
#        #msg = b"\xff" + msg
#        #msg = int.from_bytes(msg, "big")
#        #if msg >= self.n:
#            #utils.raiseException("RSA.PrivateKey.sign", "Message must be less than N")
#        #return utils.int2bytes(pow(msg, self.d, self.n))
#    
#    def dump(self):
#        return("#AbelRSA Private Key#{}#{}#{}#".format(base64.b64encode(utils.int2bytes(self.n)).decode(), base64.b64encode(utils.int2bytes(self.e)).decode(), base64.b64encode(utils.int2bytes(self.d)).decode()))
#    
#    def load(keyStr):
#        utils.checkParamTypes("RSA.PrivateKey.load", [keyStr], [{str}])
#        keyStr = keyStr.strip()
#        if keyStr.count("#") != 5:
#            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
#        keyStr = keyStr.strip('#')
#        name, n, e, d = keyStr.split('#')
#        if name != "AbelRSA Private Key":
#            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
#        try:
#            n = int.from_bytes(base64.b64decode(n.encode()), 'big')
#            e = int.from_bytes(base64.b64decode(e.encode()), 'big')
#            d = int.from_bytes(base64.b64decode(d.encode()), 'big')
#            return PrivateKey(n, e, d)
#        except:
#            utils.raiseException("RSA.PrivateKey.load", "keyStr is not a valid AbelRSA Private Key")
#    
#    def getPublicKey(self):
#        return PublicKey(self.n, self.e)
#    
#    def __eq__(self, other):
#        if isinstance(other, self.__class__):
#            return self.n == other.n and self.e == other.e and self.d == other.d
#        else:
#            return False    


#def genKeyPair(length=1024, custom_e=None):
#    utils.checkParamTypes("RSA.genKeyPair", [length, custom_e], [{int}, {type(None), int}])
#    if custom_e is None:
#        e = DEFAULT_E
#    else:
#        e = custom_e
#    p = utils.randomPrime(length // 8, length // 2)
#    remLength = length - int(math.log(p, 2))
#    q = utils.randomPrime(remLength, remLength + 2)
#    n = p * q
#    while egcd(n, e)[2] != 1:
#        p = utils.randomPrime(length // 8, length // 2)
#        remLength = length - math.log(p, 2)
#        q = utils.randomPrime(remLength, remLength + 2)
#        n = p * q
#    phi = (p - 1) * (q - 1)
#    d = modularInverse(e, phi)
#    return (PublicKey(n, e), PrivateKey(n, e, d))


#def loadKey(key):
#    utils.checkParamTypes("RSA.loadKey", [key], [{bytes, str, PublicKey, PrivateKey}])
#    if isinstance(key, bytes):
#        key = key.decode()
#    if isinstance(key, str):
#        try:
#            return PrivateKey.load(key)
#        except:
#            return PublicKey.load(key)
#    else:
#        return key