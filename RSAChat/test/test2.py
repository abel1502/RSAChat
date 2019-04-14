def tmain():
    from .. import network, utils
    import time
    
    network.Server(port=8889)
    network.SERVER.start()
    time.sleep(150)
    network.SERVER.abort()
    
    
    utils.exit()