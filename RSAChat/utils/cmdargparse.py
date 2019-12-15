class BaseException(Exception):
    def __init__(self, text=""):
        self.text = text

class TolerableException(BaseException):
    def __init__(self, parsed="", text="Unexpected end"):
        self.parsed = parsed
        super().__init__(text=text)

class UntolerableException(BaseException):
    pass


class CmdArgParser:
    def __init__(self, data):
        self.cur = ""
        self.pos = 0
        self.data = data
    
    def next(self):
        if not self.pos < len(self.data):
            self.cur = ""
            return True
        self.cur = self.data[self.pos]
        self.pos += 1
        return False
    
    def end(self):
        return self.pos >= len(self.data) - 1
   
    def readUntil(self, until, escapeable=False):
        lRes = []
        lEnd = False
        while not lEnd and self.cur != until:
            if self.cur == "\\":
                try:
                    lTmp, lEnd = self.parseEscape()
                except TolerableException as e:
                    raise TolerableException(parsed=("".join(lRes) + e.parsed), text=e.text)
                lRes.append(lTmp)
            else:
                lRes.append(self.cur)
                lEnd = self.next()
        return "".join(lRes), lEnd
    
    def parseArgument(self, escapeable=True, until=" "):
        if self.cur in ("\"", "'"):
            lQuote = self.cur
            lEnd = self.next()
            if lEnd:
                raise TolerableException(parsed=lQuote, text="Quote not closed")
            try:
                lRes, lEnd = self.readUntil(lQuote, escapeable=escapeable)
            except TolerableException as e:
                raise TolerableException(parsed=(lQuote + e.parsed), text=e.text)
            if lEnd:
                raise TolerableException(parsed=(lQuote + lRes), text="Quote not closed")
            lEnd = self.next()
            if not lEnd and self.cur != until:
                raise UntolerableException(text="Extra appendix after closing quote")
            return lRes, lEnd
        lRes, lEnd = self.readUntil(until)  # Nothing to prepend
        return lRes, lEnd
    
    def parseEscape(self):
        assert self.cur == "\\"  # Only occurs if used incorrectly, not with bad input
        lEnd = self.next()
        if lEnd:
            raise TolerableException(parsed="\\", text="Escape sequence not completed")
        try:
            lRes = ("\\" + self.cur).encode().decode("unicode-escape")
        except UnicodeDecodeError as e:
            raise UntolerableException(text="Bad escape sequence ({})".format("\\" + self.cur))
        return lRes, self.next()
    
    def getArguments(self, tolerate=False):
        lArgs = []
        lEnd = self.next()
        lPartial = False
        while not lEnd:
            try:
                lArg, lEnd = self.parseArgument()
            except TolerableException as e:
                if tolerate:
                    return lArgs + [e.parsed]
                raise e
            lArgs.append(lArg)
            if lEnd or self.next():
                break
        return lArgs
