#!/usr/bin/python


from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import json
import pika
import struct
import IPy
import time
import urlparse

PORT_NUMBER = 8081

HOSTNAME = "localhost"
RECEIVE_EXCHANGE = "receive_exchange"

MAX_INCOMING_LENGTH = 4096
PKT_TYPE_HTTP_POST = 3

class myHandler(BaseHTTPRequestHandler):
	requestline = ''
	request_version = 'HTTP/1.0'

	def handle(self):
		now = int(time.time()*1000)

		amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(
			host=HOSTNAME))
		amqp_chan = amqp_conn.channel();

		header_str = ''
		while True:
			byte = self.rfile.read(1)
			header_str += byte
			if len(header_str) > 3 and header_str[-4:] == '\r\n\r\n':
				break
		headers = header_str.split('\n')
		for header in headers:
			val = header.split(': ')
			if val[0] == 'Content-Length':
				length = int(val[1])
			if header[0:4] == 'POST':
				posts = header.split(" ")
				post_str = posts[1]

		poststr = self.rfile.read(length)
		data = urlparse.parse_qs(poststr)

		# Get the IPv6 address in integer form
		try:
			addr = IPy.IP(IPy.IPint(self.client_address[0])).v46map().int()
		except ValueError:
			# This was apparently already an IPv6 address
			addr = IPy.IPint(self.client_address[0]).int()

		port = self.client_address[1]

		amqp_pkt = struct.pack("!BQQHQ",
			PKT_TYPE_HTTP_POST,
			addr>>(64*8),
			addr,
			port,
			now)

		amqp_pkt += post_str + json.dumps(data)

		print(amqp_pkt)

		amqp_chan.basic_publish(exchange=RECEIVE_EXCHANGE, body=amqp_pkt,
			routing_key='')

		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		# Send the html message
		self.wfile.write("[0]")
		return

	def log_message(self, format, *args):
		return

try:
	# Create a web server and define the handler to manage the incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)

	# Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
