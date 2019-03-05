import socket

s = socket.socket()
s.bind(("", 8888))
s.listen(5)
c, a = s.accept()
print(a)
pkg = (lambda x: len(x).to_bytes(2, 'big') + x)(b'TEST 123')
print(pkg)
c.send(pkg)
c.close()