import sys
import getopt
import time
import random
import os
import math

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.max_data_size = 1372
        self.windowsize = 5
        self.max_window_size = 5
        self.connectiontimeout = 10
        self.timeout = 0.5
        self.seqno = 0
        self.wnd = []
        self.filename = filename
        self.dupacks = 0

    # Main sending loop.
    def start(self):
        """ Send a file or get input from stdin. Send all data
        in order, reliably to receiver. """
        msg = self.infile
        # if no file or stdin, exit
        if not self.filename:
            return
        self.lastseqno = math.ceil(os.path.getsize(filename)/self.max_data_size)
        # turn file into packet generator
        packets = self.get_packets(msg)
        
        # get start packet
        startpacket = packets.next()
        
        # exit on failure to establish connection
        if not self.initiate_connection(startpacket):
            return
        # connection has been established

        # set timer to keep track of when we hear from receiver
        connectiontimer = time.time()
        
        # main sending/receiving loop
        while True:

            # refresh the buffer
            self.get_window(packets, self.windowsize)

            # if window is empty, we exit the loop
            if not self.wnd:
                break

            # send a window of packets to receiver
            for packet in self.wnd:
                self.send(packet)
                
            # wait for response
            while True:
                response = self.receive(self.timeout)
                if not response:
                    # connection lost
                    if time.time() > connectiontimer + self.connectiontimeout:
                        return
                    # packet timeout

                    # resize the window since we got a timeout
                    self.windowsize -= 1
                    self.windowsize = max(1, self.windowsize)
                    break
                else:
                    connectiontimer = time.time()
                    
                if self.checkresponse(response, self.seqno, self.seqno + len(self.wnd)):
                    # increase the window size since were getting a response from receiver
                    self.windowsize += 1
                    self.windowsize = min(self.max_window_size, self.windowsize)

                    # ack is valid, update seqno, buffer new packets, send newly buffered packets
                    self.handle_new_ack(response, packets)

                # if window is empty, we exit the loop
                if not self.wnd:
                    break

                # three dupacks, resend the first packet in the buffer
                if self.dupacks > 2:
                    # decrease the size of the window since we got three dupacks
                    self.windowsize -= 1
                    self.windowsize = max(1, self.windowsize)
                    self.send(self.wnd[0])

                    
    def initiate_connection(self, start_packet):
        """ Send a start packet and wait to hear back from
        receiver before sending more packets. Returns true if a connection is 
        initiated, returns false otherwise"""
        # to keep track of when we started trying to initiate connection
        connectiontimer = time.time()
        # Loop until connection is established
        while self.seqno == 0:
            self.send(start_packet)
            response = self.receive(self.timeout)
            # Ensure the connection is properly established.
            if self.checkresponse(response):
                self.seqno += 1
            # Could not establish a connection.
            elif time.time() - connectiontimer > self.connectiontimeout:
                # print "Cannot establish connection to Receiver"
                return False
        return True

    def checkresponse(self, resp, minack= 0, maxack= 1):
        """ Helper. Checks if the ack packet is not 
        corrupted and that the seqno in the ack is 
        the next seqno. Also checks if resp is null or Ack is non-int."""
        # response is nil, not a valid response
        if not resp:
            return False
        # get the pieces of the response packet
        spacket = self.split_packet(resp)
        msg_type, ackno = spacket[0], spacket[1]
        
        # msgs from receiver should only be of type 'ack'
        if msg_type != 'ack': 
            return False
    
        #if ackno is not an int, exit
        try:
            ackno = int(ackno)
        except ValueError:
            return False

        # keep track of dupacks to resend lost packet(s)
        if ackno == minack:
            self.dupacks += 1
        else:
            self.dupacks = 0

        # make sure checksum is valid, and the ackno is in the sequence of acknos we are expecting
        return Checksum.validate_checksum(resp) and ackno > minack and ackno <= maxack
     
    def get_packets(self, infile, seqno=0):
        """ Yield the packets, in order with appropriate 
        flags for start, data, end. If all data fits in 
        start packet, there is no data packet."""
        def segment_data(msg, seg_size):
            """ 
            To deal with data larger than the max packet size,
            we take in the original message, and return a 
            generator to yield segments of size seg_size.
            """
            segment = None
            while segment != '':
                segment = bytes(msg.read(seg_size))
                yield segment
            # end function segment_data

        # create and yield the start packet
        msg_type = 'start'
        segments = segment_data(infile, self.max_data_size)
        seg_buffer = [segments.next(), segments.next()]
        packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
        yield packet

        # all other packets should be data packets. yield them.
        # if all the data fit in the start packet, skip to end packet
        seqno += 1
        if seg_buffer[0] != '':
            seg_buffer.append(segments.next())
            msg_type = 'data'
            while seg_buffer[1] != '':
                packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
                yield packet
                seg_buffer.append(segments.next())
                seqno += 1

        # create and yield the end packet
        msg_type = 'end'
        packet = self.make_packet(msg_type, seqno, seg_buffer.pop(0))
        yield packet

    def get_window(self, packets, wnd_size):
        """ Modify the sending window of self by adding
        packets until the sending buffer is full. Will not
        overwrite existing packets in the buffer. """
        # when there are no new packets left to send, return nil
        while len(self.wnd) < wnd_size:
            try:
                self.wnd.append(packets.next())
            except StopIteration:
                break

    def handle_timeout(self):
        pass

    def handle_new_ack(self, ack, packets):
        ackno = int(self.split_packet(ack)[1])
        
        # # three dupacks, resend the first packet in the buffer
        # if self.dupacks > 2:
        #     self.send(self.wnd[0])
        #     # decrease the size of the window since we got three dupacks
        #     self.windowsize -= 1
        #     self.windowsize = max(1, self.windowsize)
        #     return

        # reset seqno; packet(s) acknowledged
        for i in range(self.seqno, ackno):
            self.wnd.pop(0)
        self.seqno = ackno
        
        prevwindowsize = len(self.wnd)
        # refresh window and send newly buffered packets
        self.get_window(packets, self.windowsize)
        for i in range(prevwindowsize, len(self.wnd)):
            self.send(self.wnd[i])

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
