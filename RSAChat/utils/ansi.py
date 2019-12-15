class CSI:
    normal = 0
    bold = 1
    faint = 2
    italic = 3
    underline = 4
    blink = 5
    reverse = 7
    conceal = 8
    crossed = 9
    no = 20  # Additive; not recommended
    
    fg = 30  # Additive
    bg = 40  # Additive
    bright = 60  # Additive
    bit8 = 5  # Prefix
    rgb = 2  # Prefix
    
    black = 0
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magneta = 5
    cyan = 6
    white = 7
    custom = 8  # Prefix
    
    def __init__(self, colorblind=False):
        self.colorblind = colorblind
    
    @staticmethod
    def eSeq(*data, type="m"):
        data = ";".join(map(str, data))
        return "\x1b[{data}{type}".format(data=data,type=type)
    
    @staticmethod
    def rgb(red, green, blue, background=False):
        plane = CSI.fg
        if background:
            plane = CSI.bg
        return CSI.eSeq(plane + CSI.custom, CSI.rgb, red, green, blue)
    
    def wrap(self, string, *csi):
        return self.eSeq(*csi) + string + self.eSeq() if not self.colorblind else string
    
    @staticmethod
    def strip(string):
        return string.replace("\x1b", "")


def hl(length=80, char="="):
    return char * length


def brace(string, left):
    right = left[::-1].translate(str.maketrans("({[</", ")}]>\\"))
    return left + string + right


def center(string, height, width, frame="", fill=" "):
    lRes = list(map(lambda x: frame + x[:width].center(width, fill) + frame, string.split("\n")))
    lFiller = frame + hl(length=width, char=fill) + frame
    lTop = (lFiller + "\n")* max(0, (height - len(lRes)) // 2)
    lBottom = ("\n" + lFiller) * max(0, (height - len(lRes) + 1) // 2)
    lRes = lTop + "\n".join(lRes) + lBottom
    if frame == "":
        return lRes
    return "{0}\n{1}\n{0}".format(hl(length=width + 2, char=frame), lRes)