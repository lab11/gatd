from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import IPy
import json
import pika
import struct
import time
import urlparse

LISTEN_HOST = ''
LISTEN_PORT = 8081

RECEIVE_EXCHANGE = "receive_exchange"

PKT_TYPE_HTTP_POST = 3

class gatdPostHandler (BaseHTTPRequestHandler):

	def do_POST(self):
		now = int(time.time()*1000)

		amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(
			host=HOSTNAME))
		amqp_chan = amqp_conn.channel();

		content_len = int(self.headers.getheader('content-length'))
		post_body   = self.rfile.read(content_len)
		data        = urlparse.parse_qs(post_body)

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

		amqp_pkt += self.path + json.dumps(data)

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
	server = HTTPServer((LISTEN_HOST, LISTEN_PORT), gatdPostHandler)

	# Wait forever for incoming HTTP requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
