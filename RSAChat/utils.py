import math
from threading import Lock
from . import cryptoRandom
import random
import sys
import configparser
import os
import threading
from urllib.request import urlopen
import time
from . import RSA


def checkParamTypes(source, args, types):
    if len(args) != len(types):
        raiseException(source, "Wrong argument count")
    i = 0
    for arg, _types in zip(args, types):
        if not isinstance(arg, tuple(_types)):
            raiseException(source, "Wrong argument {} type - expected {}, got {}".format(i, ' or '.join(map(lambda x: x.__name__, _types)), type(arg)))
        i += 1


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
        raiseException("utils.randomPrime", "Minimal length must be less or equal to maximal length")
    _min, _max = 2 ** (max(0, minl - 1)), 2 ** (maxl)
    #p = customRandom.randOdd(_min, _max)
    p = random.randint(_min, _max) * 2 + 1
    while not isPrime(p):
        #p = customRandom.randOdd(_min, _max)
        p = random.randint(_min, _max) * 2 + 1
    return p


def int2bytes(n):
    return n.to_bytes(max(math.ceil(math.log(n, 256)), 1), "big")


def raiseException(source, text):
    raise Exception("<ERROR in {}: {}>".format(source, text))


def showWarning(source, text):
    print("<WARNING in {}: {}>".format(source, text), file=sys.stderr)


def openIni(path):
    parser = configparser.ConfigParser()
    if not (os.path.exists(path) and os.path.isfile(path)):
        showWarning("utils.openIni", "Ini file missing")
        if not os.path.exists(os.path.dirname(path)):
            os.mkdir(os.path.dirname(path))
        if os.path.exists(path) and not os.path.isfile(path):
            raiseException("utils.openIni", "Ini config path points to a directory")
        if not os.path.exists(path):
            open(path, "w").close()
    parser.read(path)
    return parser


class IniParser:
    def __init__(self, iniFilePath):
        checkParamTypes("utils.IniParser", [iniFilePath], [{str}])
        self.filePath = iniFilePath
        self.parser = openIni(iniFilePath)
        
    def get(self, section, key, default=None, expected=str):
        checkParamTypes("utils.IniParser.get", [section, key], [{str}, {str}])
        try:
            return expected(self.parser.get(section, key))
        except:
            return default
        
    def set(self, section, key, value):
        checkParamTypes("utils.IniParser.set", [section, key], [{str}, {str}])
        self.parser.set(section, key, str(value))
        with open(self.filePath, "w") as f:
            self.parser.write(f)


class Thread(threading.Thread):
    """https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread"""
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
    def stop(self):
        self._stop_event.set()
    def stopped(self):
        return self._stop_event.is_set()


def startThread(target, args=tuple()):
    t = Thread(target=target, args=args)
    t.start()
    return t


def randomBytes(length):
    return random.randint(0, 256 ** length).to_bytes(length, "big")


#def pad(data, length):
    #assert length > len(data)
    #if length - len(data) == 1:
        #return '\x01' + data
    #return (length - len(data)).to_bytes(2, "big") * (length - len(data)) + data

#def unpad(data):
    #length = data[0]
    #return data[length:]


def loadRSAKey(encKey, PRIV=False, PUB=False):
    lKey = encKey
    if isinstance(encKey, bytes):
        lKey = lKey.decode()
    if isinstance(lKey, str):
        lKey = RSA.Key.load(lKey)
    
    if (lKey.isPub() and PUB) or (lKey.isPriv() and PRIV):
        return lKey
    assert False


def dumpRSAKey(key, PRIV=False, PUB=False):
    key = loadRSAKey(key, PRIV, PUB)
    if (key.isPub() and PUB) or (key.isPriv() and PRIV):
        return key.dump()
    assert False


# ? Bytes support?
def csi(*payload):
    return "\x1b[{}m".format(";".join(map(str, payload)))

def wrapCsi(data, *payload):
    return csi(*payload) + str(data) + csi()

def stripCsi(data):
    return data.replace("\x1b", "")


def generateNickname(key, color=True):  # TODO: Support bw
    key = loadRSAKey(key, PUB=True)  # ? Allow priv?
    lRnd = random.Random(key.fields["n"])  # ? Hopefully sufficient
    #lRnd = random.Random(key.getFingerprint())
    #lUrl = "https://gist.github.com/abel1502/7490688318d63cbaed234374e88ded74/raw/{}.txt"
    #lFirsts = tuple(urlopen(lUrl.format("adjectives")).read().decode().split("\n"))
    #lSeconds = tuple(urlopen(lUrl.format("nouns")).read().decode().split("\n"))
    with open("config/adjectives.txt", "r") as f:
        data = f.read()
        import hashlib
        assert hashlib.sha256(data.encode()).hexdigest() == "aa7f9d272f709fd962a433531e1bc8afa4df9d4fd22ca8611a53e22030a90be5"
        lFirsts = tuple(data.split("\n"))
    with open("config/nouns.txt", "r") as f:
        data = f.read()
        assert hashlib.sha256(data.encode()).hexdigest() == "dd26cd1322a6d43ee631fb4ae86e386e03dd868d2cb5dfcc2cf25d40ddc20f25"
        lSeconds = tuple(data.split("\n"))
    lColors = (31, 32, 33, 34, 35, 36)
    lFirst = lRnd.choice(lFirsts)
    lSecond = lRnd.choice(lSeconds)
    if color:
        lColor = lRnd.choice(lColors)
    else:
        lColor = 0
    return wrapCsi("{}_{}".format(lFirst, lSecond), lColor)


class NotEnoughDataException(Exception):
    pass


class Buffer:
    def __init__(self, *args, blocking=False, **kwargs):
        self._buf = bytearray(*args, **kwargs)
        self.blocking = blocking
        self._lock = Lock()  # Non-blocking? Timeout?

    def put(self, data):
        #self._lock.acquire()
        self._buf.extend(data)
        #self._lock.release()

    def get(self, size):
        #self._lock.acquire()
        while self.blocking and len(self) < size:
            pass
        if len(self) < size:
            raise NotEnoughDataException()
        self._lock.acquire()
        data = bytes(self._buf[:size])
        self._buf[:size] = b''
        self._lock.release()
        return data
    
    def getAll(self):
        return self.get(len(self))

    def peek(self, size):
        return self._buf[:size]

    def __len__(self):
        return len(self._buf)


def log(*data):
    print(*data)
    sys.stdout.flush()