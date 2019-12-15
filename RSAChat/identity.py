from enum import Enum
import re
from RSAChat import utils


class NicknameType(Enum):
    none = 0
    mnemonic = 1
    custom = 2


class Identity:  # TODO
    def __init__(self, key=None, keyFingerprint=None, nickname=None, nicknameCert=None):
        self.setKey(key)
        self.setKeyFingerprint(keyFingerprint)
        self.setNickname(nickname)
        self.setNicknameCert(nicknameCert)
    
    def setKey(self, key):
        if key is Not None:
            key = utils.loadRSAKey(key, PUB=True, PRIV=True)
        self.key = key
    
    def setKeyFingerprint(self, keyFingerprint):
        if keyFingerprint is None and self.key is not None:
            keyFingerprint = self.key.getFingerprint()
        if keyFingerprint is not None and self.key is not None:
            assert self.key.checkFingerprint(keyFingerprint)
        self.keyFingerprint = keyFingerprint
    
    def setNickname(self, nickname):
        if nickname is not None:
            self.nicknameType = NicknameType.custom
        elif self.key is not None:
            self.nicknameType = NicknameType.mnemonic
            nickname = self.key.getNickname(color=True)  # ?
        else:
            self.nicknameType = NicknameType.none
        self.nickname = nickname
    
    def setNicknameCert(self, nicknameCert):
        pass  # TODO
    
    def __str__(self):
        pass
    
    def verifyKeyFingerprint(self):
        pass
    
    def verifyNicknameCert(self):
        pass
    
    """
    Key:
        #PUB#...#...#
        #PRIV#...#...#...#
    Mnemonic Nickname:
        #...#
    Nickname (Cannot have "#" in it. Most likely, "a-zA-Z0-9_"):
        ...
    Fingerprint (on its own or at the end):
        <...>
    """
    @classmethod
    def parse(cls, text):
        if re.match(utils.anyKeyPattern, text):
            _, lKey, lFingerprint = re.split(utils.anyKeyPattern, text, 1)
            lKey = utils.loadRSAKey(lKey, PUB=True, PRIV=True)
            if lFingerprint:
                lFingerprint = re.fullmatch(utils.fingerprintPattern, lFingerprint)[1]
                assert self.verifyKeyFingerprint()
                return cls(key=lKey, keyFingerprint=lFingerprint)
            return cls(key=lKey)
        if re.match(utils.mnemonicPattern, text):
            _, lMnemonic, lFingerprint = re.split(utils.mnemonicPattern, text, 1)
            if lFingerprint:
                lFingerprint = re.fullmatch(utils.fingerprintPattern, lFingerprint)[1]
                return cls(mnemonic=lMnemonic, keyFingerprint=lFingerprint)
            return cls(mnemonic=lMnemonic)
        if re.match(utils.nicknamePattern, text):
            _, lNickname, lFingerprint = re.split(utils.nicknamePattern, text, 1)
            if lFingerprint:
                lFingerprint = re.fullmatch(utils.fingerprintPattern, lFingerprint)[1]
                return cls(nickname=lNickname, keyFingerprint=lFingerprint)
            return cls(nickname=lNickname)
        if re.fullmatch(utils.fingerprintPattern, text):
            lFingerprint = re.fullmatch(utils.fingerprintPattern, lFingerprint)[1]
            return cls(keyFingerprint=lFingerprint)
        assert False


class Target:  # Target for a message: ? an identity / a nickname / a group / ALL
    def __init__(self):
        pass