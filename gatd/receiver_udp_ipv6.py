#!/usr/bin/env python3

import ipaddress
import socket

import arrow
import pika
import setproctitle
import xsocket

import gatdConfig
import gatdLog

l = gatdLog.getLogger('recv-UDP-ipv6')

setproctitle.setproctitle('gatd:recv-udp6')


def receive ():

	# Create a UDP socket to listen for incoming packets
	s = xsocket.xsocket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
	s.bind(("::", gatdConfig.receiver_udp_ipv6.PORT))

	l.info('Created xsocket to listen for UDP packets on port {}'.format(gatdConfig.receiver_udp_ipv6.PORT))

	while True:
		data, src, dst = s.recvfromto()
		now = arrow.utcnow().isoformat()

		src_addr = ipaddress.ip_address(src[0])
		src_port = src[1]

		dst_addr = ipaddress.ip_address(dst[0])

		pkt = {}
		pkt['src'] = 'receiver_udp_ipv6'
		pkt['src_addr'] = str(src_addr)
		pkt['src_port'] = src_port
		pkt['time_utc_iso'] = now
		pkt['data'] = data

		# Send the packet to the queue
		amqp_chan.basic_publish(exchange='xch_receiver_udp_ipv6',
		                        body=pkt,
		                        routing_key=str(dst_addr))


# Setup the connection to RabbitMQ
def pika_on_channel (amqp_chan):

	# Create the receive exchange if it doesn't exist.
	amqp_chan.exchange_declare(exchange='xch_receiver_udp_ipv6',
	                           exchange_type='direct',
	                           durable='true')

	# Make sure there is a queue for unknown packets
	amqp_chan.queue_declare(queue='receive-unknown',
	                        durable=True)
	amqp_chan.queue_bind(queue='receive-unknown',
	                     exchange='xch_receiver_udp_ipv6',
	                     routing_key='unknown')

	while True:
		try:
			receive()
		except:
			l.exception('Error occurred in UDP receive loop.')


def pika_on_connection (unused_connection):
	amqp_conn.channel(pika_on_channel)


amqp_conn = pika.SelectConnection(
				pika.ConnectionParameters(
					host=gatdConfig.rabbitmq.HOST,
					port=gatdConfig.rabbitmq.PORT,
					credentials=pika.PlainCredentials(
						gatdConfig.receiver_udp_ipv6.RMQ_USERNAME,
						gatdConfig.receiver_udp_ipv6.RMQ_PASSWORD)),
				pika_on_connection
			)
amqp_conn.ioloop.start()

