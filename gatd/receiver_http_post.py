#!/usr/bin/env python3

"""
Listen for HTTP posts and make the headers and content a packet.
"""

import http.server
import ipaddress
import pickle
import socketserver

import arrow
import pika

import gatdConfig
import gatdLog

l = gatdLog.getLogger('recv-HTTP-POST')


class gatdPostHandler (http.server.BaseHTTPRequestHandler):

	def do_POST (self):
		try:
			now = arrow.utcnow().isoformat()

			amqp_conn = pika.BlockingConnection(
							pika.ConnectionParameters(
								host=gatdConfig.rabbitmq.HOST,
								port=gatdConfig.rabbitmq.PORT,
								virtual_host=gatdConfig.rabbitmq.VHOST,
								credentials=pika.PlainCredentials(
									gatdConfig.blocks.RMQ_USERNAME,
									gatdConfig.blocks.RMQ_PASSWORD)
						))
			amqp_chan = amqp_conn.channel();

			content_len = int(self.headers.get('content-length'))
			post_body   = self.rfile.read(content_len)

			receiver_id = self.path
			paths = receiver_id.split('/')
			for p in paths:
				if len(p) > 0:
					receiver_id = p
					break
			else:
				l.error('No UUID found in POST URL.')
				raise Exception('No UUID found')

			if 'X-Real-IP' in self.headers:
				# This script is running behind nginx, and self.client_address
				# is just local host, so nginx appends headers so we don't
				# lose that information.
				src_addr = ipaddress.ip_address(self.headers['X-Real-IP'])
			else:
				src_addr = ipaddress.ip_address(self.client_address[0])
			port = self.client_address[1]

			l.debug('Got POST. src:{}, len:{}'.format(src_addr, content_len))

			pkt = {}
			pkt['src'] = 'receiver_http_post'
			pkt['src_addr'] = str(src_addr)
			pkt['src_port'] = port
			pkt['time_utc_iso'] = now
			pkt['headers'] = dict(self.headers)
			pkt['data'] = post_body

			pkt_pickle = pickle.dumps(pkt)

			l.debug('Sending packet to rabbitmq key:{} length:{}'.format(receiver_id, len(pkt_pickle)))

			amqp_chan.basic_publish(exchange='xch_scope_a',
			                        body=pkt_pickle,
			                        routing_key=receiver_id)

			self.send_response(200)
			self.end_headers()
			self.wfile.write('Success'.encode('utf8'))

		except:
			l.exception('Error occurred handling POST')
			self.send_response(400)
			self.end_headers()
			self.wfile.write('Error'.encode('utf-8'))

	def log_message(self, format, *args):
		return

class ForkingHTTPServer(socketserver.ForkingMixIn, http.server.HTTPServer):
	def finish_request(self, request, client_address):
		request.settimeout(30)
		# "super" can not be used because BaseServer is not created from object
		http.server.HTTPServer.finish_request(self, request, client_address)

try:
	# Create a web server and define the handler to manage the incoming request
	server = ForkingHTTPServer(('', 25101), gatdPostHandler)

	l.info('HTTP POST Receiver on port 25101')

	# Wait forever for incoming HTTP requests
	server.serve_forever()

except KeyboardInterrupt:
	l.info('^C received, shutting down the web server')
	server.socket.close()
