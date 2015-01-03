#!/usr/bin/env python3

import ipaddress
import pickle
import socket
import sys

import arrow
import pika
import setproctitle
import xsocket

import gatdConfig
import gatdLog

l = gatdLog.getLogger('recv-UDP-ipv4')

setproctitle.setproctitle('gatd:recv-udp4')


def receive (amqp_chan):

	# Create a UDP socket to listen for incoming packets
	s = xsocket.xsocket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	s.bind(("0.0.0.0", gatdConfig.receiver_udp_ipv4.PORT))

	l.info('Created xsocket to listen for UDP packets on port {}'\
		.format(gatdConfig.receiver_udp_ipv4.PORT))

	while True:
		data, src, dst = s.recvfromto()
		now = arrow.utcnow().isoformat()

		src_addr = ipaddress.ip_address(src[0])
		src_port = src[1]

		dst_addr = ipaddress.ip_address(dst[0])

		if len(data) < 36:
			l.warn('Received packet that is too short. src:{}, len:{}'\
				.format(src_addr, len(data)))
			continue

		uuid = data[0:36].decode('ascii')
		data = data[36:]

		pkt = {}
		pkt['src'] = 'receiver_udp_ipv4'
		pkt['src_addr'] = str(src_addr)
		pkt['src_port'] = src_port
		pkt['time_utc_iso'] = now
		pkt['data'] = data

		pkt_pickle = pickle.dumps(pkt)

		l.debug('Sending packet key:{} len:{}'.format(uuid, len(data)))

		# Send the packet to the queue
		amqp_chan.basic_publish(exchange='xch_scope_a',
		                        body=pkt_pickle,
		                        routing_key=uuid)


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

