#!/usr/bin/env python3

import http.server
import ipaddress
import socketserver

import arrow
import pika
import setproctitle

setproctitle.setproctitle('gatd:recv-httpp')

import gatdConfig
import gatdLog

l = gatdLog.getLogger('recv-HTTP-POST')


class gatdPostHandler (http.server.BaseHTTPRequestHandler):

	def do_POST (self):
		now = arrow.utcnow().isoformat()

		amqp_conn = pika.BlockingConnection(
						pika.ConnectionParameters(
							host=gatdConfig.rabbitmq.HOST,
							port=gatdConfig.rabbitmq.PORT,
							credentials=pika.PlainCredentials(
								gatdConfig.receiver_http_post.RMQ_USERNAME,
								gatdConfig.receiver_http_post.RMQ_PASSWORD)
					))
		amqp_chan = amqp_conn.channel();

		content_len = int(self.headers.getheader('content-length'))
		post_body   = self.rfile.read(content_len)

		receiver_id = self.path
		if len(receiver_id) > 0 and receiver_id[0] == '/':
			receiver_id = receiver_id[1:]

		src_addr = ipaddress.ip_address(self.client_address[0])
		port = self.client_address[1]

		l.info('Got POST. src:{}, len:{}'.format(src_addr, content_len))

		pkt = {}
		pkt['src'] = 'receiver_http_post'
		pkt['src_addr'] = str(src_addr)
		pkt['src_port'] = src_port
		pkt['time_utc_iso'] = now
		pkt['headers'] = dict(self.headers)
		pkt['data'] = post_body

		amqp_chan.basic_publish(exchange='xch_receiver_http_post',
		                        body=pkt,
		                        routing_key=receiver_id)

		self.send_response(200)

	def log_message(self, format, *args):
		return

class ForkingHTTPServer(socketserver.ForkingMixIn, http.server.HTTPServer):
	def finish_request(self, request, client_address):
		request.settimeout(30)
		# "super" can not be used because BaseServer is not created from object
		BaseHTTPServer.HTTPServer.finish_request(self, request, client_address)

try:
	# Make sure the exchange exists
	amqp_conn = pika.BlockingConnection(
					pika.ConnectionParameters(
						host=gatdConfig.rabbitmq.HOST,
						port=gatdConfig.rabbitmq.PORT,
						credentials=pika.PlainCredentials(
							gatdConfig.receiver_http_post.RMQ_USERNAME,
							gatdConfig.receiver_http_post.RMQ_PASSWORD)
				))
	amqp_chan = amqp_conn.channel();

	amqp_chan.exchange_declare(exchange='xch_receiver_http_post',
	                           exchange_type='direct',
	                           durable='true')
	amqp_chan.close()

	# Create a web server and define the handler to manage the incoming request
	server = ForkingHTTPServer(('', 25101), gatdPostHandler)

	# Wait forever for incoming HTTP requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
