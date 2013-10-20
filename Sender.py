import sys
import getopt
import cStringIO

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.max_data_size = 1372

    # Main sending loop.
    def start(self):
        seqno = 0
        msg_type = None
        curr_seg = None
        next_seg = None
        while msg_type is not 'end':
            msg = filename and self.infile or raw_input("message to send > ")
            segments = self.segment_data(msg, self.max_data_size)
            try:
                curr_seg = segments.next() if not curr_seg else next_seg
                next_seg = segments.next()
            except StopIteration:
                next_seg = False

            msg_type = 'data'
            if seqno == 0:
                msg_type = 'start'
            elif next_seg is None or curr_seg == 'done':
                msg_type = 'end'

            packet = self.make_packet(msg_type, seqno, curr_seg)
            curr_seg = next_seg
            print(packet)
            seqno += 1


    def segment_data(self, msg, seg_size):
        """ 
        To deal with data larger than the max packet size,
        we take in the original message, and yield segments
        of size seg_size back to the calling function.
        """
        msg = cStringIO.StringIO(msg) if not hasattr(msg, 'read') else msg
        while True:
            segment = bytes(msg.read(seg_size))
            if segment == '':
                yield None
            else:
                yield segment

    def handle_timeout(self):
        pass

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print msg
 

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
