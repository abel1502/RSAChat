def tmain():
    from .. import network, utils, RSA, credentials
    import time
    
    key1 = RSA.PrivateKey.load(credentials.get("Client", "key"))
    pKey1 = key1.getPublicKey()
    key2 = RSA.PrivateKey.load("#AbelRSA Private Key#AwjZltppCYnSZoEEuMit79wKiG6VIsm19ie7UNDoj+hTPZIfs+/5rKC+11GLJ+U0pi3m/+NktL82MIGCJgUO5H0SvEIzh83QKH4Hszg/Lka4sBgdMUMSKftBtgI9pC39R11Wi7GOe3YiOZDVsz+AcUM2BV/72A72McUh6Jz3/W3ZW/bfaIgPIH9HtdguLW9qVaHoUJFO4Knp64pLyJoWtWwTTzzZ9qjIP2MxACm4YVWm/SIFfN2K3RLfavEob8qKLGIJ7S5D3jrT2D9atEh5SFylGjsnwVbnC4ciDQ4riPe+vXqwc5Q9TUDZ4NyfhiMle8uijLRdgafyooJeRLfSCVs=#AQAB#28EJnnE2JImjO34Fc6dYgcts+rMvaxYRMv4XB3GyO8tIUIytTwY24iX6LPQLbhgtpjCBVGcJhkmjAQ+7B5VF52ekX6nKEdt/iN9OwGuHALSAA+JGLC34OD5HaWzcg7HxPSMdUzX2EN3voNwC38TKxXODo7pPTTQxsg08iyLPywE+zvCj8S6UFciqcLh/RbhnW0by4RgKAmMoKKhuppn8ISq7Eq1Mj5WJcvZcf4OzSI5b8si8i9AGqsiR6WG8ZTIfOJgaPlx+QwXAX5HhhqfafHbHuBDSSBQcNvFMm8JzhLXAj867s/ZwkSoXK26rj7uhfOfT6tn84iF/tx28y2Mv0Q==#")
    pKey2 = key2.getPublicKey()    
    
    network.connect_client("localhost", 58887, privKey=key2)
    #network.connect_client("example.com", 80, privKey=key2)
    time.sleep(10)
    #network.CLIENT.aioClient[1].sendMsg("Hello, I guess?)... <[Randomness4security]>", pKey2)  # Probably add third key as the other client
    #time.sleep(5)
    
    utils.exit()