Jason Ibrahim ee122-dw
Abdulhamid Fallaha ee122-nw

This project was about a 6 in terms of challenging. It was much better than project 1 because it was just a lot more
straight forward in that we knew what we had to do, and exactly what it should output.

It definitely was challenging. The most challening part was designing our own test cases,
as there we so many different edge cases to test.

The extra credit options we implemented were (1) Variable Size Sliding Window and (3) Accounting for variable RTT

(1) Variable Size Sliding Window
	How it works:
		We have an instance variable self.windowsize which keeps track of the size of the buffer we are using to
		buffer in new packets. On a timeout, we decrement this variable by 1, on a triple dupack we decrement this
		variable by 1, and on a successful response from the receiver, we increment this value by 1. We make sure
		that the windowsize is never below 1 or above 5. Using this value, is a function called get_window, which
		fills up the buffer up to the size specified by windowsize. We send packets from this buffer using the
		windowsize variable, so the buffer size fluctuates depending on network conditions.

(3) Variable RTT
	How it works:
		We use an exponential weighted average of the packet_sent times and the ack_received times
		with an alpha of 0.5 to determine what the estimated RTT is. Once we have calculated this value,
		we set an instance variable called self.timeout = estimatedRTT. We use this new timeout value
		in determining the response time from the receiver in self.receive(self.timeout).

		Using this increased the speed of our transfers significantly. We noticed a speed increase of
		more than 10 times in the RandomDropTest for an image file that was 1.2 MB.
