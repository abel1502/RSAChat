def tmain():
    #from .. import protocol
    #from .. import utils
    #print(protocol._EPACKET.parse(b'\x01\x00\x00\x0eThis is EPDATA')[1].EPDATA)
    #print(protocol._EPACKET(EPID=1, EPDATA=b'This is EPDATA').encode())
    #print(protocol.SPACKET.parse(b'\x00\x0eThis is SPDATA\x00\x0dThis is SPKEYsaltsaltsaltsalt')[1].fields)
    
    from .. import utils
    from .. import network
    from .. import protocol
    import time
    network.Client("localhost", port=8889)
    network.CLIENT.start()
    p = protocol._EPACKET(EPID=1, EPDATA=b'#AbelRSA Public Key#Ae8fHQWV6v/d4KR9N7PwjCZHIwqbZXZGjKlDDn2nhsy44bB26CYAfi9p1R5UDHnoUwwGQXaTNLawvRHbBZGXJCNKR0gwTXHvkrt5Q6CU0airaByBAjZ3p0zfm0W1#AQAB#')
    network.CLIENT.aioClient[1].transport.write(p.encode())
    network.CLIENT.abort()
    
    #from .. import RSA
    #print(RSA.genKeyPair(2048)[1].dump())
    
    #key = RSA.PrivateKey.load("#AbelRSA Private Key#Ae8fHQWV6v/d4KR9N7PwjCZHIwqbZXZGjKlDDn2nhsy44bB26CYAfi9p1R5UDHnoUwwGQXaTNLawvRHbBZGXJCNKR0gwTXHvkrt5Q6CU0airaByBAjZ3p0zfm0W1#AQAB#Admc54QKTksHEPYHmZsUhNuwvIJO95VWEwNuU5Q7BiUZbAnUavra9+5igHtn/hGgqzI1zChFoGnClhgSaYs9iqsHREHMj7o0AATE5zHeTSU3KOlh7OaiXL6m6kFB#")
    #print(key.getPublicKey().dump())
    
    #key = RSA.PrivateKey.load("#AbelRSA Private Key#CHu2zkbyL3g1ERCCkXRDx7wk5SQVUy2QRk3YzbeCFOeGY7Vp1FUBV8vN1BnBMzX0V+xML9/CHEfAG0s4GcXv9p0aNJNgwywiRnr+AD6O8RDpW3002gpSxM0yWTbC3fA/2r45vfxVhZEZBXDlp1DJrHqKopcKz/KlsCxpiPIYr3iQ66CxxBaJRYCrc7Rja6ki7W2icaYvgH0pQUAlleRyVaEhLHHtdr93CgED+Xn8hKj5dPhMcmOWbSXOs0vxupTwx48lVeHfBYKiS5ShvCv+VCeLm6Wui0Ohga6qgJpU/BSkz3Usvsn3mPH3mc1V+RIsH4q7AVEJ3n3nx/6lC9sg2Ds=#AQAB#J0SB7FR6uUC0Y0kJGkITfXppTkK4c011h/jQl23ZtOoAKYqVVUgl70B0gla091fIszQZdYFMA5wcojqMdMDHA8Yyhyuru8OO5LBtDrSE9VpS1iu7eY5PkqpDZLMXUj3FVcUzgzmEpb//EjCE2vgaj0iscfC3G9sVGWh7Gm2J1rMiEq5neeAOUcCqrwD+cim5xnHEKLiifVsgRpV5AdyWosSP+iWakck+qeOlaeFcJ9gWpoZmlKycfGa2eA5K9rGMwnXoXNTDACsml/KDPlDybnL3Qt05HATcrDeFqZFk0A+f46hrtRIVzFznbLMQs6DtyAL+yPopd/oklywC6Nh50Q==#")
    
    #pub = key.getPublicKey()
    #print(pub.dump())
    #text = 'Test for AbelRSA crypto module.'
    #m = pub.encrypt(text.encode())
    #print(text)
    #print(m)
    #print(key.decrypt(m).decode())
    
    utils.exit()