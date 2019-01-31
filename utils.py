import math
import cryptoRandom
import random


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
        raise Exception("<ERROR in utils.modularInverse(): GCD(n, p) != 1>")
    k = -k
    while m < 0:
        m += p
        k += n
    return m


def checkParamTypes(source, args, types):
    if len(args) != len(types):
        raise Exception("<ERROR in {}: Wrong argument count>".format(source))
    i = 0
    for arg, _types in zip(args, types):
        if type(arg) not in _types:
            raise Exception("<ERROR in {}: Wrong argument {} type - expected {}, got {}>".format(source, i, ' or '.join(map(lambda x: x.__name__, _types)), type(arg)))
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
        raise Exception("<ERROR in utils.randomPrime(): Minimal length must be less or equal to maximal length>")
    _min, _max = 2 ** (max(0, minl - 1)), 2 ** (maxl)
    #p = customRandom.randOdd(_min, _max)
    p = random.randint(_min, _max) * 2 + 1
    while not isPrime(p):
        #p = customRandom.randOdd(_min, _max)
        p = random.randint(_min, _max) * 2 + 1
    return p


def int2bytes(n):
    return n.to_bytes(math.ceil(math.log(n, 256)), "big")

