from . import utils
__DEBUG__ = "test"


def main():
    pass
    utils.exit()


if __DEBUG__ == "test":
    from .test import test
    test.tmain()
    #from .test import test2
    #test2.tmain()
else:
    main()
