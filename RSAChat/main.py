from RSAChat import network
from RSAChat import utils

__DEBUG__ = 0


def serverMain():
    priv = utils.RSA.loadKey("#PRIV#BkrdzKQvPR4PgZT4fh7ZrOfTwhOXG25zb3pEtO5rOIvyqQi8aRNZCGcVUXiPX5zYVQJXzfcc6/VKJrc6EYMHB0GMwYguiA0E0Hwk6tDpWVpgDTmP1IoC53oPuYsRj3DZHwx372gk85YTjhbu2Q7+uVprVgLiStgL+TKRJiGKZypXIAOE3nVBu+Rgd/sKvLJRASEdc6ILghBUvSpn0NdYyUQ6EPnowjAAUFvf1D8om4AggoYVOhDavKTSeoOJI/erwB+x90VhSm02bDpyUernR7rdTZJLlZWkcyBrZL8pu6BY285rGv2U5Yu5tGeqptUWMSep9EGTBDpFGsN7ufcYq1c=#AQAB#BDfzBTxZky7xFF3sTpmeM8ZkeGur1a8x4t3k7CwfZBSnBd4eeo+HFBQP/cPG00IS4sMkXKg8EpErOlOCsbTXZGz00dbb40hfHurr0SVoHAhz9snNfJ9eHRP/MNRkXHc6iQ9R5QY8J7ZIu+zyCkF8UoWlCk/6qFS5ikL1fsvjvxBmQXgqbRFT3hkbW/ezO5uAlCXFRweS77FzesEgtUr3nFVCZG1eobamCgY1RycQv2tuNzZK80xU92gqza5PR311UO18jr2HTqzjnp5ZVSFnoYY2Ar4SaaEopMGDUJHz0JDqyWicsSuNxoTFcLRuHbyV8q91/0+XcoEKvdYagsN6y1k=#", PRIV=True)
    #priv = utils.RSA.genKeyPair(1024)[1]
    utils.logIdentity(priv)
    network.start_server(aServerKey=priv)


def clientMain():
    priv = utils.RSA.loadKey("#PRIV#BNGbE0h9qCE8XY2BLCCbpIbnFOm3HgnMvA6SPoJkbo8KIeBRwb+Wr146rbMtyOKDaaHXPg99yAe+Dd4t91zdEDNU7DGXIsSpvT1TDaM59LyuP5hTdi7gFUlTpph/VhNrsxkdkVAlppBW4AV88M0C8WQpS/8ykj36c65RcND9h7ED#AQAB#BC0EXxSN2BpdLpFG5E+psU06ibPzfTNu2XUjJMpocCrC1BKJpwX5diWJYieJQLGSwgJ+/Yf9L1AOUgQ8/0TZSYDecwrrqEN78Nmcwx25ZGTBnNq/s76vVk0bt6Sg8QjF66dox3V7AU9bLpAdqhjrRRTIAL0UrQGSLBERUF+WDuSR#", PRIV=True)
    #priv = utils.RSA.genKeyPair(1024)[1]
    utils.logIdentity(priv)
    network.connect_client("localhost", aClientKey=priv)


def main():
    lMode = (input("Would you like to act as a client or a server? [C]/[s]: ").lower() + "c")[0]
    if lMode == "s":
        serverMain()
    else:
        clientMain()


#main()

if __DEBUG__ == 1:
    from .test import test
    test.tmain()
elif __DEBUG__ == 2:
    from .test import test2
    test2.tmain()
else:
    main()
