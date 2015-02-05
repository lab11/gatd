#!/usr/bin/env python3

"""
Listen for UDP packets from an IPv6 host.
"""

import ipaddress
import pickle
import socket
import sys

import arrow
import pika
import xsocket

import gatdConfig
import gatdLog

l = gatdLog.getLogger('recv-UDP-ipv6')


def receive (amqp_chan):

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

		pkt_pickle = pickle.dumps(pkt)

		l.debug('Sending packet to rabbitmq with routing key:{}'.format(str(dst_addr)))

		# Send the packet to the queue
		amqp_chan.basic_publish(exchange='xch_scope_a',
		                        body=pkt_pickle,
		                        routing_key=str(dst_addr))


# Setup the connection to RabbitMQ
def pika_on_channel (amqp_chan):

	while True:
		try:
			receive(amqp_chan)
		except KeyboardInterrupt:
			l.info('ctrl+c, exiting')
			amqp_chan.close()
			sys.exit(0)
		except:
			l.exception('Error occurred in UDP receive loop.')


def pika_on_connection (unused_connection):
	amqp_conn.channel(pika_on_channel)


amqp_conn = pika.SelectConnection(
				pika.ConnectionParameters(
					host=gatdConfig.rabbitmq.HOST,
					port=gatdConfig.rabbitmq.PORT,
					virtual_host=gatdConfig.rabbitmq.VHOST,
					credentials=pika.PlainCredentials(
						gatdConfig.blocks.RMQ_USERNAME,
						gatdConfig.blocks.RMQ_PASSWORD)),
				pika_on_connection
			)
amqp_conn.ioloop.start()

