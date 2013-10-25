import random

from BasicTest import *

"""
This test sends too many dupacks. Sometimes it will drop all of the packets in the queue.
"""
class DupAcks(BasicTest):
    def handle_packet(self):
        b = []
        for p in self.forwarder.in_queue:
            if random.randint(0,1):
                for i in range(0,300):
                    b.append(p)
            else :
                b.append(p)
            for p in b:
                self.forwarder.out_queue.append(p)


        # empty out the in_queue
        self.forwarder.in_queue = []