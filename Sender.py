import sys
import getopt
import cStringIO
import time
import random
import pdb
import select

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.max_data_size = 1372
        self.windowsize = 3
        self.timeout = 0.5
        self.seqno = 0
        self.wnd = []

    # Main sending loop.
    def start(self):
        """ Send a file or get input from stdin. Send all data
        in order, reliably to receiver. """
        end_transmission = False
        while not end_transmission:
            
            end_transmission = self.handle_file(self.infile) \
            if filename and self.infile else self.handle_stdin()
                  
    def handle_file(self, infile):
        """ To send data from file included with -f flag in sysargs.
        If data is fetched from stdin, it is converted to a file and
        this function is called. """

        # Initialize variables
        windowsize = self.windowsize

        # Initialize the generators that will yield the packets...
        segments = self.segment_data(infile, self.max_data_size)
        packets = self.get_packets(segments)

        # To keep track of which packets get acked
        acked = {}
        for i in range(self.seqno, self.seqno + len(self.wnd)):
            acked[i] = False

        # Attempt to establish a connection...
        start_packet = packets.next()
        self.initiate_connection(start_packet)
        acked[0] = True
        # Connection established!

        # Grab the first window of packets to send
        self.get_window(packets, windowsize)

        # Main sending/receiving loop
        while True:

            # Send the whole window
            for packet in self.wnd:
                self.send(packet)

            # Wait to hear back from receiver. If receiver sends ack,
            # set appropriate flag in acked to True
            for packet in self.wnd:
                response = self.receive(self.timeout)
                if response:
                    ackno = int(self.split_packet(response)[1])
                    for j in range(0, ackno):
                        acked[j] = True

            # Delete in order acked packets from the window
            # to make room for more packets to fill the buffer
            for i in range(self.seqno, len(acked.keys())):
                if acked[i]:
                    self.wnd.pop(0)
                    self.seqno += 1
                else:
                    break

            # Refresh the window
            self.get_window(packets, windowsize)
            # pdb.set_trace()
            if not self.wnd:
                break

        # Reset seqno and exit loop
        self.seqno = 0
        return True

    def handle_stdin(self):
        """ To send data that is input via stdin."""
        msg = sys.stdin

        # Check if stdin is empty, return 
        if not select.select([msg,],[],[],0.0)[0]:
            return True

        # If stdin is not a file that can be read, coerce it to a StringIO object 
        msg = cStringIO.StringIO(msg) if msg and not hasattr(msg, 'read') else msg

        # Pass the buck to handle_file
        self.handle_file(msg)

        # Make sure to return True or we'll loop forever
        return True

    def initiate_connection(self, start_packet):
        """ Send a start packet and wait to hear back from
        receiver before sending more packets."""
        while self.seqno == 0:
            self.send(start_packet)
            response = self.receive(self.timeout)
            if response:
                self.seqno += 1

    def get_packets(self, segments, seqno=0):
        """ Yield the packets, in order with appropriate 
        flags for start, data, end. If all data fits in 
        start packet, there is no data packet."""
        msg_type = 'start'
        seg_buffer = [segments.next(), segments.next()]
        packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
        yield packet
        seqno += 1
        if seg_buffer[0] is not '':
            seg_buffer.append(segments.next())
            msg_type = 'data'
            while seg_buffer[1] != '':
                packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
                yield packet
                seg_buffer.append(segments.next())
                seqno += 1
        msg_type = 'end'
        packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
        yield packet

    def segment_data(self, msg, seg_size):
        """ 
        To deal with data larger than the max packet size,
        we take in the original message, and return a 
        generator to yield segments of size seg_size.
        """
        segment = None
        while segment is not '':
            segment = bytes(msg.read(seg_size))
            yield segment

    def get_window(self, packets, wnd_size):
        """ Modify the sending window of self by adding
        packets until the sending buffer is full. Will not
        overwrite existing packets in the buffer. """
        while len(self.wnd) < wnd_size:
            try:
                self.wnd.append(packets.next())
            except StopIteration:
                break

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
