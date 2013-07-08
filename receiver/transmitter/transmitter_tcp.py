import socket
import sys
import time

HOST, PORT = "inductor.eecs.umich.edu", 4002
data = "a"

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	# Connect to server and send data
	sock.connect((HOST, PORT))
	for i in range(0,3):
		sock.sendall("\x42\x43\x44EFG")
		time.sleep(1)

finally:
	sock.close()
