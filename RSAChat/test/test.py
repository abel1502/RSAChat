def tmain():
    from .. import RSA
    from .. import utils
    
    #pub, priv = RSA.genKeyPair(2048)
    priv = utils.loadRSAKey("#PRIV#AwjZltppCYnSZoEEuMit79wKiG6VIsm19ie7UNDoj+hTPZIfs+/5rKC+11GLJ+U0pi3m/+NktL82MIGCJgUO5H0SvEIzh83QKH4Hszg/Lka4sBgdMUMSKftBtgI9pC39R11Wi7GOe3YiOZDVsz+AcUM2BV/72A72McUh6Jz3/W3ZW/bfaIgPIH9HtdguLW9qVaHoUJFO4Knp64pLyJoWtWwTTzzZ9qjIP2MxACm4YVWm/SIFfN2K3RLfavEob8qKLGIJ7S5D3jrT2D9atEh5SFylGjsnwVbnC4ciDQ4riPe+vXqwc5Q9TUDZ4NyfhiMle8uijLRdgafyooJeRLfSCVs=#AQAB#28EJnnE2JImjO34Fc6dYgcts+rMvaxYRMv4XB3GyO8tIUIytTwY24iX6LPQLbhgtpjCBVGcJhkmjAQ+7B5VF52ekX6nKEdt/iN9OwGuHALSAA+JGLC34OD5HaWzcg7HxPSMdUzX2EN3voNwC38TKxXODo7pPTTQxsg08iyLPywE+zvCj8S6UFciqcLh/RbhnW0by4RgKAmMoKKhuppn8ISq7Eq1Mj5WJcvZcf4OzSI5b8si8i9AGqsiR6WG8ZTIfOJgaPlx+QwXAX5HhhqfafHbHuBDSSBQcNvFMm8JzhLXAj867s/ZwkSoXK26rj7uhfOfT6tn84iF/tx28y2Mv0Q==#", PRIV=True)
    pub = priv.getPublicKey()
    #print(utils.dumpRSAKey(priv, PRIV=True))
    
    #utils.log(utils.wrapCsi("Hello", 31, 1))  # 8 (conseal) works!
    utils.log(pub.getReprName())
    
    return
    #priv.encrypt(b"Hello World")
    
    msg = b"Hello World! "
    enc = pub.encrypt(msg)
    print(enc)
    dec = priv.decrypt(enc)
    print(dec)