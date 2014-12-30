#!/usr/bin/env python3

import ipaddress
import socket

import arrow
import pika
import setproctitle
import xsocket

import gatdConfig
import gatdLog
import gatdMongo

l = gatdLog.getLogger('recv-UDP-ipv6')

setproctitle.setproctitle('gatd:recv-udp6')


# Keep track of which IPv6 addresses we know have queues associated with them
known_ips = {}

def receive (mi, amqp_chan):

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
		pkt['src_addr'] = str(src_addr)
		pkt['src_port'] = src_port
		pkt['time_utc_iso'] = now
		pkt['data'] = data

		# Find the profile of this incoming packet
		if dst_addr in known_ips:
			route_key = str(dst_addr)

		else:
			route_key = 'unknown'

		# Send the packet to the queue
		amqp_chan.basic_publish(exchange='xch_receiver_udp_ipv6',
		                        body=pkt,
		                        routing_key=route_key)



def update_profile_state (mi, amqp_chan):
	known_ips = {}

	# Get a list of all known profiles and make sure the queues from the receive
	# exchange exist. These need to be present to ensure packets have somewhere
	# to go and are not lost.
	profiles = mi.getProfiles()
	for profile in profiles:
		profile_uuid = profile['uuid']

		# Each profile is made a series of blocks.
		# We just care about the udp receiver type
		if 'blocks' not in profile:
			l.debug('No blocks found in profile "{}" ("{}")'.format(profile_uuid, profile['name']))
			continue

		# Iterate all blocks and setup the queues for each UDP receiver block
		for block in profile['blocks']:
			if block['type'] == 'receiver_udp_ipv6':
				unique_ip = ipaddress.ip_address(block['dst_addr'])

				# Find all connections that originate from this block
				for connection in profile['connections']:
					src = connection['source_uuid']
					tar = connection['target_uuid']

					if src == block['uuid']:

						# Create a queue for each connection
						l.info('Adding queue for profile {} with connection {}-{}'.format(profile_uuid, src, tar))

						# Add a queue with a well specified name with the
						# same routing key.
						queue_name = 'udp-receiver-ipv6_{}_{}'.format(src, tar)
						amqp_chan.queue_declare(queue=queue_name,
					                            durable=True)
						amqp_chan.queue_bind(queue=queue_name,
						                     exchange=gatdConfig.rabbitmq.XCH_UDP_RECEIVE,
						                     routing_key=str(unique_ip))

				known_ips[unique_ip] = True


# Setup the connection to RabbitMQ
def pika_on_channel (amqp_chan):

	# Create the receive exchange if it doesn't exist.
	# Use direct exchange because we will sent all received packets to it
	#  and directed into the correct queue based on the profile. The `profile_id`
	#  will be the routing key.
	amqp_chan.exchange_declare(exchange='xch_receiver_udp_ipv6',
	                           exchange_type='direct',
	                           durable='true')

	# Make sure there is a queue for unknown packets
	amqp_chan.queue_declare(queue='receive-unknown',
	                        durable=True)
	amqp_chan.queue_bind(queue='receive-unknown',
	                     exchange='xch_receiver_udp_ipv6',
	                     routing_key='unknown')


	# Setup a connection to the Mongo database
	mi = MongoInterface.MongoInterface(host=gatdConfig.mongodb.HOST,
	                                   port=gatdConfig.mongodb.PORT,
	                                   username=gatdConfig.receiver_udp_ipv6.MDB_USERNAME,
	                                   password=gatdConfig.receiver_udp_ipv6.MDB_PASSWORD)

	# Load all known UDP blocks and create queues for them if they don't
	# exist
	update_profile_state(mi, amqp_chan)

	while True:
		try:
			receive(mi, amqp_chan)
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

