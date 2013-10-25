import random

from BasicTest import *

"""
This test corrupts random packets.
"""
class CorruptTest(BasicTest):
    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.randint(1,5) == 1:
                p.msg_type = 'nonsense'
            elif random.randint(1,5) == 2:
                p.checksum = 5
            elif random.randint(1,5) == 3:
                p.seqno = 40139840239842
            elif random.randint(1,5) == 4:
                p.data = 'Hamed is a really cool guy.'
            self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []