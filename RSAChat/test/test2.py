def tmain():
    from .. import network, utils
    import time
    
    network.Server(port=8889)
    network.SERVER.start()
    time.sleep(150)
    network.SERVER.abort()
    
    #network.startServer(port=8889)
    #while network.SERVER is None or len(network.SERVER.clients) == 0:
        #pass
    #c = network.SERVER.clients[0]
    #print(c)
    #pkg = (lambda x, y: x.to_bytes(1, 'big') + len(y).to_bytes(2, 'big') + y)(0, b'TEST 123')
    #print(pkg)
    #c.send(pkg)
    #time.sleep(2)
    #c.abort()
    
    
    
    #s = network.Server()
    #s.listen("", 8887)
    #s.startMain()
    #while len(s.clients) < 1:
        #pass
    #print(list(s.clients.keys())[0])
    #c = s.clients[list(s.clients.keys())[0]]
    #print(c)
    #pkg = (lambda x, y: x.to_bytes(1, 'big') + len(y).to_bytes(2, 'big') + y)(0, b'TEST 123')
    #print(pkg)
    #c._send(pkg)
    #time.sleep(2)
    #c.abort()
    #s.abort()
    utils.exit()