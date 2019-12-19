import math
from threading import Lock
import random
import sys
import configparser
import os
import threading
from urllib.request import urlopen
import time
import random
import types


class Decorator:
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.initParametric(*args, **kwargs)
    
    def initParametric(self, *args, **kwargs):
        pass
        
    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
    
    @classmethod
    def parametric(cls, *args, **kwargs):
        return lambda func: cls(func, *args, **kwargs)


class MethodDecorator(Decorator):
    def __get__(self, instance, owner=None):
        if instance is not None:
            return types.MethodType(self, instance)
        if owner is not None:
            return types.MethodType(self, owner)
        assert False
    
    def __call__(self, wrappedSelf, *args, **kwargs):
        return self.function(wrappedSelf, *args, **kwargs)


class StaticDecorator(Decorator):
    def __get__(self, instance, owner=None):
        return self


class Singleton:
    _instance = None
    
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


from . import ansi
from . import RSA


class _RndSeeder(Singleton):
    def __init__(self):
        random.seed(os.urandom(256))

_RndSeeder.getInstance()


def checkParamTypes(source, args, types):
    if len(args) != len(types):
        raiseException(source, "Wrong argument count")
    i = 0
    for arg, _types in zip(args, types):
        if not isinstance(arg, tuple(_types)):
            raiseException(source, "Wrong argument {} type - expected {}, got {}".format(i, ' or '.join(map(lambda x: x.__name__, _types)), type(arg)))
        i += 1


def int2bytes(n):
    return n.to_bytes(max(math.ceil(math.log(n, 256)), 1), "big")


def raiseException(source, text):
    raise Exception("<ERROR in {}: {}>".format(source, text))


def showWarning(source, text):
    log("<WARNING in {}: {}>".format(source, text), file=sys.stderr)


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
    return random.getrandbits(8 * length).to_bytes(length, "big")


class ColorProvider(Singleton, ansi.CSI):
    pass


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


def queueGet(queue):
    if len(queue) == 0:
        raise NotEnoughDataException()
    return queue.popleft()


def log(*data):
    print(*data)
    flush()


def flush():
    sys.stdout.flush()


def logIdentity(key):
    key = RSA.loadKey(key, PRIV=True)
    log("Your identity:\n{priv}\n{pub}\n\n{nick}\n".format(priv=key.dump(), pub=key.getPublicKey().dump(), nick=key.getPublicKey().getReprName()))


def exit():
    os._exit(0)
