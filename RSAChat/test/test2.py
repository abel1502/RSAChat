def tmain():
    from .. import network, utils
    s = network.Server()
    s.listen("", 8887)
    s.startMain()
    while len(s.clients) < 1:
        pass
    print(list(s.clients.keys())[0])
    c = s.clients[list(s.clients.keys())[0]]
    pkg = (lambda x, y: x.to_bytes(1, 'big') + len(y).to_bytes(2, 'big') + y)(0, b'TEST 123')
    print(pkg)
    c._send(pkg)
    c.abort()
    s.abort()
    utils.exit()