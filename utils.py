import math
import cryptoRandom
import random
import sys
import configparser


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


def checkParamTypes(source, args, types):
    if len(args) != len(types):
        raiseException(source, "Wrong argument count")
    i = 0
    for arg, _types in zip(args, types):
        if type(arg) not in _types:
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
    # TODO: Implement)
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
    return n.to_bytes(math.ceil(math.log(n, 256)), "big")


def raiseException(source, text):
    raise Exception("<ERROR in {}(): {}>".format(source, text))


def showWarning(source, text):
    print("<WARNING in {}(): {}>".format(source, text), file="")


def openIni(path):
    if Config.path is None:
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