from . import general
import random  # secrets?
import math
import base64
import os
from enum import Enum
import hashlib

#DEFAULT_E = config.get("Crypto", "Default_E", 65537, int)
DEFAULT_E = 65537


def isPrime(n, k=10):
    # TODO: Check
    if n < 20:
        return (n in {2, 3, 5, 7, 11, 13, 17, 19})
    if n % 2 == 0:
        return False
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for __ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def randomPrime(minl, maxl):
    if minl > maxl:
        raise Exception("randomPrime", "Minimal length must be less or equal to maximal length")
    _min, _max = 2 ** (max(0, minl - 1)), 2 ** (maxl)
    p = random.randint(_min, _max) * 2 + 1
    while not isPrime(p):
        p = random.randint(_min, _max) * 2 + 1
    return p


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
        raise Exception("modularInverse", "GCD(n, p) != 1")
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
        return general.int2bytes(pow(data, self.fields[exp], self.fields["n"]))
    
    def pad(self, data):
        return b"\xff" + data
    
    def unpad(self, data):
        return data[1:]
    
    def encrypt(self, data, exp="e"):
        # Data must be bytes (or bytearray?)... ?
        padAmount = (-len(data)) % (self.blockLen - 1)
        lDataBuf = general.Buffer(data)
        lFirstBlock = self.pad(lDataBuf.get(self.blockLen - 1 - padAmount))
        lRes = int.from_bytes(self._apply(lFirstBlock, exp), "big")
        while len(lDataBuf) > 0:
            lRes = lRes * self.fields["n"] + int.from_bytes(self._apply(self.pad(lDataBuf.get(self.blockLen - 1)), exp), "big")
        return general.int2bytes(lRes)
    
    def decrypt(self, data, exp="d"):
        data = int.from_bytes(data, "big")
        lRes = []
        while data > 0:
            lRes.append(self.unpad(self._apply(general.int2bytes(data % self.fields["n"]), exp)))
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
        _enc = lambda val: base64.b64encode(general.int2bytes(val)).decode()
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
    
    def getFingerprint(self, hasher=hashlib.sha256, hex=True):
        lHash = hasher(self.dump().encode())
        if hex:
            return lHash.hexdigest()
        return lHash.digest()
    
    def checkFingerprint(self, fingerprint, hasher=hashlib.sha256, hex=True):
        return self.getFingerprint(hasher=hasher, hex=hex) == fingerprint
    
    def getNickname(self):
        return MnemonicProvider.getInstance().generate(self)
    
    def getReprName(self):
        lNickname = self.getNickname()
        lFingerprint = self.getFingerprint()  # ? Is trimming okay?
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
    n = e
    while egcd(n, e)[2] != 1:
        p = randomPrime(length // 8, length // 2)
        remLength = length - math.log(p, 2)
        q = randomPrime(remLength, remLength + 2)
        n = p * q
    phi = (p - 1) * (q - 1)
    d = modularInverse(e, phi)
    return (Key(n, e), Key(n, e, d))


pubKeyPattern = "#PUB#.+?#.+?#"
privKeyPattern = "#PRIV#.+?#.+?#.+?#"
anyKeyPattern = "#(PUB|PRIV)#.+?#.+?#(.+?#|)"


def loadKey(encKey, PRIV=False, PUB=False):
    lKey = encKey
    if isinstance(encKey, bytes):
        lKey = lKey.decode()
    if isinstance(lKey, str):
        lKey = Key.load(lKey)
    
    if (lKey.isPub() and PUB) or (lKey.isPriv() and PRIV):
        return lKey
    assert False


def dumpKey(key, PRIV=False, PUB=False):
    key = loadKey(key, PRIV, PUB)
    return key.dump()


mnemonicPattern = "(#[a-zA-Z\-]+_[a-zA-Z\-]+#)"
mnemonicFormat = "#{first}_{second}#"
nicknamePattern = "([a-zA-Z0-9_\-]+)"
nicknameFormat = "{}"
fingerprintPattern = "<([a-zA-Z0-9]+)>"
fingerprintFormat = "<{}>"

class MnemonicProvider(general.Singleton):
    def __init__(self):
        with open("config/adjectives.txt", "r") as f:
            _tmp = f.read()
            import hashlib
            assert hashlib.sha256(_tmp.encode()).hexdigest() == "aa7f9d272f709fd962a433531e1bc8afa4df9d4fd22ca8611a53e22030a90be5"
            self.firsts = tuple(_tmp.split("\n"))
        with open("config/nouns.txt", "r") as f:
            _tmp = f.read()
            assert hashlib.sha256(_tmp.encode()).hexdigest() == "dd26cd1322a6d43ee631fb4ae86e386e03dd868d2cb5dfcc2cf25d40ddc20f25"
            self.seconds = tuple(_tmp.split("\n"))

    def generate(self, key):  # TODO: Support bw
        key = loadKey(key, PUB=True)  # ? Allow priv?
        lRnd = random.Random(key.fields["n"])  # ? Hopefully sufficient
        #lRnd = random.Random(key.getFingerprint())
        #lUrl = "https://gist.github.com/abel1502/7490688318d63cbaed234374e88ded74/raw/{}.txt"
        #lFirsts = tuple(urlopen(lUrl.format("adjectives")).read().decode().split("\n"))
        #lSeconds = tuple(urlopen(lUrl.format("nouns")).read().decode().split("\n"))
        lColors = (31, 32, 33, 34, 35, 36)
        lFirst = lRnd.choice(self.firsts)
        lSecond = lRnd.choice(self.seconds)
        lRes = mnemonicFormat.format(first=lFirst, second=lSecond)
        lColor = lRnd.choice(lColors)
        lRes = general.ColorProvider.getInstance().wrap(lRes, lColor)
        return lRes

MnemonicProvider.getInstance()