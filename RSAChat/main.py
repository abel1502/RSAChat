from . import utils
from enum import Enum
__DEBUG__ = ("test", 1)

class MODE(Enum):
    SERVER = 0
    CLIENT = 1
    def __str__(self):
        return "server" if self is MODE.SERVER else "client"

def main():
    mode = (lambda x: MODE.SERVER if x.lower() == 's' else MODE.CLIENT)(input("Would you like to act as a client or a server? ([C]/[s]): "))
    print("Acting as", mode)
    if mode is MODE.SERVER:
        pass
    else:
        pass
    utils.exit()


if __DEBUG__[0] == "test":
    if __DEBUG__[1] == 1:
        from .test import test
        test.tmain()
    elif __DEBUG__[1] == 2:
        from .test import test2
        test2.tmain()
else:
    main()
