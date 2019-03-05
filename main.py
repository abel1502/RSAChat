import utils
__DEBUG__ = "test"


def __main__():
    pass
    
    utils.exit()


if __DEBUG__ == "test":
    import sys
    sys.path.append("./test")
    import _test
    _test.tmain()
elif __name__ == "__main__":
    main()
