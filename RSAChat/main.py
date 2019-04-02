from . import utils
__DEBUG__ = ("test", 1)


def main():
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
