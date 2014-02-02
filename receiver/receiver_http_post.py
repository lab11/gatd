#!/usr/bin/env python2

import BaseHTTPServer
import SocketServer
import IPy
import json
import pika
import string
import struct
import time
import urlparse
import os
import sys

sys.path.append(os.path.abspath('../config'))
import gatdConfig


class gatdPostHandler (BaseHTTPServer.BaseHTTPRequestHandler):

	def do_POST(self):
		now = int(time.time()*1000)

		amqp_conn = pika.BlockingConnection(
		            pika.ConnectionParameters(host=gatdConfig.rabbitmq.HOST))
		amqp_chan = amqp_conn.channel();

		content_len = int(self.headers.getheader('content-length'))
		post_body   = self.rfile.read(content_len)
		data        = urlparse.parse_qs(post_body)
		profile_id  = string.strip(self.path, '/')

		# Get the IPv6 address in integer form
		try:
			addr = IPy.IP(IPy.IPint(self.client_address[0])).v46map().int()
		except ValueError:
			# This was apparently already an IPv6 address
			addr = IPy.IPint(self.client_address[0]).int()

		port = self.client_address[1]

		amqp_pkt = struct.pack("!BQQHQ",
			gatdConfig.pkt.TYPE_HTTP_POST,
			addr>>(64*8),
			addr,
			port,
			now)

		amqp_pkt += profile_id + json.dumps(data)

		amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
		                        body=amqp_pkt,
		                        routing_key='')

		self.send_response(200)
	#	self.send_header('Content-type','text/html')
	#	self.end_headers()
	#	# Send the html message
	#	self.wfile.write("[0]")
	#	return

	def log_message(self, format, *args):
		return

class ForkingHTTPServer(SocketServer.ForkingMixIn, BaseHTTPServer.HTTPServer):
	def finish_request(self, request, client_address):
		request.settimeout(30)
		# "super" can not be used because BaseServer is not created from object
		BaseHTTPServer.HTTPServer.finish_request(self, request, client_address)

try:
	# Create a web server and define the handler to manage the incoming request
	server = ForkingHTTPServer(('', gatdConfig.receiver.PORT_HTTP_POST),
	                           gatdPostHandler)

	# Wait forever for incoming HTTP requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
