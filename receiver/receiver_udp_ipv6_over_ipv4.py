import base64
import json
import pika
import socket
import struct
import time

"""
Receives UDP packets from IPv6 nodes that were "tunneled" over IPv4
"""

HOST = "0.0.0.0"
UDP_IPV4_RECEIVE_PORT = 16284

MAX_INCOMING_LENGTH = 4096
PKT_TYPE_UDP = 0

HOSTNAME = "localhost"
RECEIVE_EXCHANGE = "receive_exchange"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, UDP_IPV4_RECEIVE_PORT))

# Setup connection to rabbitmq
amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
amqp_chan = amqp_conn.channel();

while True:
	try:
		data, addr = sock.recvfrom(MAX_INCOMING_LENGTH)

		current_time = int(round(time.time()*1000))

		pkt = json.loads(data)
		origdata = base64.b64decode(pkt['data'])

		amqp_pkt = struct.pack("!BQQHQ",
			PKT_TYPE_UDP,
			pkt['src']>>(64),
			int(pkt['src']&0xFFFFFFFFFFFFFFFF),
			int(pkt['srcport']),
			current_time)

		amqp_pkt += origdata

		amqp_chan.basic_publish(exchange=RECEIVE_EXCHANGE, body=amqp_pkt,
			routing_key='')


	except KeyboardInterrupt:
		quit()
	except:
		pass