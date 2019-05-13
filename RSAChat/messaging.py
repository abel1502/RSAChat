from collections import deque
from . import utils
from . import protocol
import time
from . import RSA

INCOMING_QUEUE = deque()
#OUTGOING_QUEUE = deque()


class Message:
    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], protocol.PPACKET):
            self.replyTo, self.text = args[0].MSG.decode().split(' ', 1)
            # Verify that is public?
            self.replyTo = RSA.loadKey(self.replyTo)
            self.timestamp = time.gmtime(args[0].TIME)
        elif len(args) == 3 and isinstance(args[0], (bytes, str, RSA.PublicKey)) and isinstance(args[1], str) and isinstance(args[2], (int, time.time_struct)):
            self.replyTo = RSA.loadKey(args[0])
            self.text = args[1]
            self.timestamp = args[2] if isinstance(args[2], time.time_struct) else time.gmtime(args[2])
