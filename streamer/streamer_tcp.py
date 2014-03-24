#!/usr/bin/env python2

import os
import sys
import struct
import socket
import SocketServer
import pika
import json
import struct

import setproctitle
setproctitle.setproctitle('gatd-s: tcp')

sys.path.append(os.path.abspath('../config'))
import gatdConfig

class ThreadedTCPRequestHandler (SocketServer.BaseRequestHandler):

	# When a client connects setup a channel to the rabbitmq server
	def setup (self):
		self.amqp_conn = pika.BlockingConnection(
			pika.ConnectionParameters(host=gatdConfig.rabbitmq.HOST,
			                          port=gatdConfig.rabbitmq.PORT,
			                          credentials=pika.PlainCredentials(
			                          	gatdConfig.rabbitmq.USERNAME,
			                          	gatdConfig.rabbitmq.PASSWORD)))
		self.amqp_chan = self.amqp_conn.channel();

	def handle (self):
		data = self.request.recv(4096)
		print data

		# data should be a JSON blob describing what data the client wants
		try:
			self.query = json.loads(data)
		except ValueError:
			# Not a valid JSON blop
			self.request.sendall("ERROR: Query was not a valid JSON string.")
			return

		# Take the query and create the first pass filter by telling the
		# stream exchange that we only want packets that have certain keys in
		# them.
		# We can do better if the query wants a specific profile because the
		# profile is included in the headers.
		keys = dict((x,struct.pack("B",0)) for x in self.query.keys())
		if 'profile_id' in self.query:
			keys['profile_id'] = self.query['profile_id']
		keys['x-match'] = "all"

		# Setup a queue to get the necessary stream
		result = self.amqp_chan.queue_declare(exclusive=True, auto_delete=True)
		self.amqp_chan.queue_bind(exchange=gatdConfig.rabbitmq.XCH_STREAM,
			queue=result.method.queue, arguments=keys)
		self.amqp_chan.basic_consume(self.process_packet,
			queue=result.method.queue, no_ack=True)
		self.amqp_chan.start_consuming()

	def finish (self):
		if self.amqp_chan.is_open:
			self.amqp_chan.close()

	# Called when each packet is received by this handler.
	def process_packet (self, ch, method, properties, body):
		# Determine if the incoming packet matches the query from the client
		pkt = json.loads(body)
		if (all((k in pkt and pkt[k]==v) for k,v in self.query.iteritems())):
			# All of the key value pairs in the query are also in the newest
			# packet
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
server = ThreadedTCPServer(('::', gatdConfig.streamer.PORT_TCP), ThreadedTCPRequestHandler)
server.serve_forever()
