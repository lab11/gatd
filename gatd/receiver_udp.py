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

l = gatdLog.getLogger('UDP-recv')

setproctitle.setproctitle('gatd:udp-recv')




# Keep track of which IPv6 addresses we know have queues associated with them
known_ips = {}

def receive (mi, amqp_chan):

	# Create a UDP socket to listen for incoming packets
	s = xsocket.xsocket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
	s.bind(("::", gatdConfig.receiver_udp.PORT))

	l.info('Created xsocket to listen for UDP packets on port {}'.format(gatdConfig.receiver_udp.PORT))

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
			# Don't recognize this destination addr, check if there is a new one
			update_profile_state(mi, amqp_chan)
			if dst_addr in known_ips:
				route_key = known_ips[dst_addr]
			else:
				route_key = 'unknown'


		# Send the packet to the queue
		amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_UDP_RECEIVE,
		                        body=pkt,
		                        routing_key=route_key)



def update_profile_state (mi, amqp_chan):
	# Get a list of all known profiles and make sure the queues from the receive
	# exchange exist. These need to be present to ensure packets have somewhere
	# to go and are not lost.
	profiles = mi.getProfiles()
	for profile in profiles:
		profile_id = profile['profile_id']

		# Each profile is made a series of blocks.
		# We just care about the udp receiver type
		if 'blocks' not in profile:
			l.debug('No blocks found in profile "{}" ("{}")'.format(profile_id, profile['name']))
			continue

		# Iterate all blocks and setup the queues for each UDP receiver block
		for block in profile['blocks']:
			if block['type'] == 'udp_receiver':
				unique_ip = ipaddress.ip_address(block['dst_addr'])

				if unique_ip not in known_ips:
					l.info('Adding queue for profile {} with IP {}'.format(profile_id, unique_ip))


					# Add a queue for the new profile_id
					queue_name = 'udp-receiver-{}'.format(block['block_id'])
					amqp_chan.queue_declare(queue=queue_name,
				                            durable=True)
					amqp_chan.queue_bind(queue=queue_name,
					                     exchange=gatdConfig.rabbitmq.XCH_UDP_RECEIVE,
					                     routing_key=str(unique_ip))

					known_ips[unique_ip] = True

			# # Save state about the profiles so we can match incoming packets
			# # to the correct profile.
			# map_dest_pid[ipaddress.ip_address(profile['udp_dst_addr'])] = profile['profile_id']
			# map_pids[profile['profile_id']] = True


# Setup the connection to RabbitMQ
def pika_on_channel (amqp_chan):

	# Create the receive exchange if it doesn't exist.
	# Use direct exchange because we will sent all received packets to it
	#  and directed into the correct queue based on the profile. The `profile_id`
	#  will be the routing key.
	amqp_chan.exchange_declare(exchange=gatdConfig.rabbitmq.XCH_UDP_RECEIVE,
	                           exchange_type='direct',
	                           durable='true')

	# Make sure there is a queue for unknown packets
	amqp_chan.queue_declare(queue='receive-unknown',
	                        durable=True)
	amqp_chan.queue_bind(queue='receive-unknown',
	                     exchange=gatdConfig.rabbitmq.XCH_UDP_RECEIVE,
	                     routing_key='unknown')


	# Setup a connection to the Mongo database
	mi = MongoInterface.MongoInterface(host=gatdConfig.mongodb.HOST,
	                                   port=gatdConfig.mongodb.PORT,
	                                   username=gatdConfig.udp_receiver.MDB_USERNAME,
	                                   password=gatdConfig.udp_receiver.MDB_PASSWORD)

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
						gatdConfig.receiver_udp.RMQ_USERNAME,
						gatdConfig.receiver_udp.RMQ_PASSWORD)),
				pika_on_connection
			)
amqp_conn.ioloop.start()

