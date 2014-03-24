#!/usr/bin/env python2

import IPy
import json
import os
import pika
import socket
import SocketServer
import struct
import sys
import time

import setproctitle
setproctitle.setproctitle('gatd-r: tcp')

sys.path.append(os.path.abspath('../config'))
import gatdConfig


MAX_INCOMING_LENGTH = 4096

class ThreadedTCPRequestHandler (SocketServer.BaseRequestHandler):

	def setup (self):
		self.amqp_conn = pika.BlockingConnection(
		                 pika.ConnectionParameters(host=gatdConfig.rabbitmq.HOST))
		self.amqp_chan = self.amqp_conn.channel();

	def handle (self):
		while True:
			data = self.request.recv(MAX_INCOMING_LENGTH)

			if len(data) == 0:
				break

			addr = IPy.IPint(self.client_address[0]).int()
			port = self.client_address[1]
			current_time = int(round(time.time()*1000))

			amqp_pkt = struct.pack("!BQQHQ",
				gatdConfig.pkt.TYPE_TCP,
				addr>>(64*8),
				addr,
				port,
				current_time)

			amqp_pkt += data

			self.amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
			                             body=amqp_pkt,
			                             routing_key='')

	def finish (self):
		if self.amqp_chan.is_open:
			self.amqp_chan.close()


class ThreadedTCPServer (SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	address_family = socket.AF_INET6

	def server_bind (self):
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(self.server_address)


# Run the receiver
server = ThreadedTCPServer(("::", gatdConfig.receiver.PORT_TCP),
                           ThreadedTCPRequestHandler)
server.serve_forever()
