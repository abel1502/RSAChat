import os
import random
#import math

random.seed(os.urandom(256))

#def randBytes(count):
#    return os.urandom(count)
#
#def randBits(count):
#    return int.from_bytes(os.urandom(count // 8 + 1), "big") % (2 ** count)
#
#def randInt(maxValue):
#    # Check to not exceed the max!!
#    tmp = int(math.log(maxValue, 256))
#    r = randBits(max(0, int(math.log(maxValue, 2)) - tmp * 8)).to_bytes(1, "big") + randBytes(tmp)
#    return int.from_bytes(r, "big")
#
#def randRange(minValue, maxValue):
#    return minValue + randInt(maxValue - minValue)
#
#def randOdd(minValue, maxValue):
#    return minValue + 1 - minValue % 2 + randInt((maxValue - minValue) // 2) * 2

