def tmain():
    from .. import utils
    from .. import network
    from .. import protocol
    import time
    
    network.Client("localhost", port=8889)
    network.CLIENT.start()
    #time.sleep(2)
    p = protocol.EPACKET(6, -1, b'Hello there!')
    #time.sleep(2)
    network.CLIENT.aioClient[1].transport.write(p.encode())
    #time.sleep(2)
    network.CLIENT.abort()
    
    #cl = network.Client("localhost", 8889)
    #cl.start()
    #time.sleep(10)
    #data = cl.recv(20)
    #print(data)
    #cl.close()
    
    #cl = network.Client()
    #cl.connect("localhost", 8887)
    #cl.startMain()
    #time.sleep(10)
    #EPID, EPDATA = cl.recievePacket()
    #print(EPID)
    #print(EPDATA.decode())
    #cl.abort()
    utils.exit()
    
    #from .. import RSA
    #print(RSA.genKeyPair(2048)[1].dump())
    
    #key = RSA.PrivateKey.load("#AbelRSA Private Key#WwozpqzV2giEfxCftmdC91Cj+/TbUkuTGw9a6dyFIMUtA/Oe6xyiKPlR3MeZWw==#AQAB#DlJuibwK8IACiBLPbVyVVf1LrSyht1UA2Rpgd7F3JkAtxxQlkBo0brKStsnMsQ==#")
    #key = RSA.PrivateKey.load("#AbelRSA Private Key#Ae8fHQWV6v/d4KR9N7PwjCZHIwqbZXZGjKlDDn2nhsy44bB26CYAfi9p1R5UDHnoUwwGQXaTNLawvRHbBZGXJCNKR0gwTXHvkrt5Q6CU0airaByBAjZ3p0zfm0W1#AQAB#Admc54QKTksHEPYHmZsUhNuwvIJO95VWEwNuU5Q7BiUZbAnUavra9+5igHtn/hGgqzI1zChFoGnClhgSaYs9iqsHREHMj7o0AATE5zHeTSU3KOlh7OaiXL6m6kFB#")
    
    #key = RSA.PrivateKey.load("#AbelRSA Private Key#CHu2zkbyL3g1ERCCkXRDx7wk5SQVUy2QRk3YzbeCFOeGY7Vp1FUBV8vN1BnBMzX0V+xML9/CHEfAG0s4GcXv9p0aNJNgwywiRnr+AD6O8RDpW3002gpSxM0yWTbC3fA/2r45vfxVhZEZBXDlp1DJrHqKopcKz/KlsCxpiPIYr3iQ66CxxBaJRYCrc7Rja6ki7W2icaYvgH0pQUAlleRyVaEhLHHtdr93CgED+Xn8hKj5dPhMcmOWbSXOs0vxupTwx48lVeHfBYKiS5ShvCv+VCeLm6Wui0Ohga6qgJpU/BSkz3Usvsn3mPH3mc1V+RIsH4q7AVEJ3n3nx/6lC9sg2Ds=#AQAB#J0SB7FR6uUC0Y0kJGkITfXppTkK4c011h/jQl23ZtOoAKYqVVUgl70B0gla091fIszQZdYFMA5wcojqMdMDHA8Yyhyuru8OO5LBtDrSE9VpS1iu7eY5PkqpDZLMXUj3FVcUzgzmEpb//EjCE2vgaj0iscfC3G9sVGWh7Gm2J1rMiEq5neeAOUcCqrwD+cim5xnHEKLiifVsgRpV5AdyWosSP+iWakck+qeOlaeFcJ9gWpoZmlKycfGa2eA5K9rGMwnXoXNTDACsml/KDPlDybnL3Qt05HATcrDeFqZFk0A+f46hrtRIVzFznbLMQs6DtyAL+yPopd/oklywC6Nh50Q==#")
    #print(RSA.getSessionKey(key.getPublicKey()))
    
    #print(key.n)
    #print("~", len(str(key.n)) * 3.3)
    #print(key.e)
    #print(key.d)
    #pub = key.getPublicKey()
    #print(pub.dump())
    #text = 'Test for AbelRSA crypto module.'
    #m = pub.encrypt(text.encode())
    #print(m)
    #print(key.decrypt(m).decode())    