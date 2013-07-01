import sys
import traceback
import time
import struct
import socket
import threading
import SocketServer
import pika
import json
import struct

HOSTNAME = "inductor.eecs.umich.edu"

HOST = "::"
PORT = 22500

STREAM_EXCHANGE = "streamer_exchange"

class ThreadedTCPRequestHandler (SocketServer.BaseRequestHandler):

	def setup (self):
		self.amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
		self.amqp_chan = self.amqp_conn.channel();

	def handle (self):
		data = self.request.recv(4096)
		print data

		# data should be a JSON blob describing what data the client wants
		try:
			query = json.loads(data)
		except ValueError:
			# Not a valid JSON blop
			self.request.sendall("ERROR: Not a valid JSON blob")
			return

		# Temporary: just match all packets that have all the same keys.
		# Ideally, this should be expanded to allow for full queries and only
		# use the amqp filtering as a rough first step.
		keys = dict((x,struct.pack("B",0)) for x in query.keys())
		keys['x-match'] = "all"

		# Setup a queue to get the necessary stream
		result = self.amqp_chan.queue_declare(exclusive=True, auto_delete=True)
		self.amqp_chan.queue_bind(exchange=STREAM_EXCHANGE,
			queue=result.method.queue, arguments=keys)
		self.amqp_chan.basic_consume(self.process_packet,
			queue=result.method.queue, no_ack=True)
		self.amqp_chan.start_consuming()

	def finish (self):
		if self.amqp_chan.is_open:
			self.amqp_chan.close()

	def process_packet (self, ch, method, properties, body):
		try:
			# Send the matching blob to the client
			a = self.request.sendall(body)
		except Exception:
			self.amqp_chan.close()
			return

class ThreadedTCPServer (SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	address_family = socket.AF_INET6

	def server_bind (self):
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(self.server_address)


# Run the server
server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
server.serve_forever()

