import socket
import time

HOSTNAME = 'inductor.eecs.umich.edu'
PORT = 4001

message = 'test'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 10000))

k = 0
while True:
	s.sendto(message + str(k), (HOSTNAME, PORT))
	k += 1
	time.sleep(3)

