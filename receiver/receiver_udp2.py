#!/usr/bin/env python3

import ipaddress
import pika
import setproctitle
import socket
import time

import xsocket

sys.path.append(os.path.abspath('../config'))
import gatdConfig

setproctitle.setproctitle('gatd-r: py-udp')


# Map of destination IP addresses to profile_id
map_dest_pid = {}

# Map of profile ids for quick lookup
map_pids = {}


def update_profile_state (mongo):
	# Get a list of all known profiles and make sure the queues from the receive
	# exchange exist. These need to be present to ensure packets have somewhere
	# to go and are not lost.
	profiles = mi.getProfiles()
	for profile in profiles:
		pid = profile['profile_id']

		# Check if this is a new profile ID
		if pid not in map_pids:

			# Add a queue for the new profile_id
			queue_name = 'receiver-{}'.format(profile['profile_id'])
			amqp_chan.queue_declare(queue=queue_name,
		                            durable=True)
			amqp_chan.queue_bind(queue=queue_name,
			                     exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
			                     routing_key=profile['profile_id'])

			# Save state about the profiles so we can match incoming packets
			# to the correct profile.
			map_dest_pid[ipaddress.ip_address(profile['dst_addr'])] = profile['profile_id']
			map_pids[profile['profile_id']] = True


# Setup the connection to RabbitMQ
amqp_conn = pika.BlockingConnection(
			pika.ConnectionParameters(
				host=gatdConfig.rabbitmq.HOST,
				port=gatdConfig.rabbitmq.PORT,
				credentials=pika.PlainCredentials(
					gatdConfig.receiver.RMQ_USERNAME,
					gatdConfig.receiver.RMQ_PASSWORD)
		))
amqp_chan = amqp_conn.channel();

# Setup a connection to the Mongo database
mi = MongoInterface.MongoInterface(host=gatdConfig.mongodb.HOST,
                                   port=gatdConfig.mongodb.PORT,
                                   username=gatdConfig.receiver.MDB_USERNAME,
                                   password=gatdConfig.receiver.MDB_PASSWORD)

# Create the receive exchange if it doesn't exist.
# Use direct exchange because we will sent all received packets to it
#  and directed into the correct queue based on the profile. The `profile_id`
#  will be the routing key.
amqp_chan.exchange_declare(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
                           exchange_type='direct',
                           durable='true')

# Make sure there is a queue for unknown packets
amqp_chan.queue_declare(queue='receive-unknown',
                        durable=True)
amqp_chan.queue_bind(queue='receive-unknown',
                     exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
                     routing_key='unknown')

# Add the rest
update_profile_state(mi)


# Create a UDP socket to listen for incoming packets
s = xsocket.xsocket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
s.bind(("::", gatdConfig.receiver.PORT_UDP))

while True:
	data, src, dst = s.recvfromto()
	now = int(time.time()*1000)

	src_addr = ipaddress.ip_address(src[0])
	src_port = src[1]

	dst_addr = ipaddress.ip_address(dst[0])

	pkt = {}
	pkt['src_addr'] = str(src_addr)
	pkt['src_port'] = src_port
	pkt['timestamp'] = now
	pkt['data'] = data

	# Find the profile of this incoming packet
	if dst_addr == gatdConfig.receiver.DEFAULT_DST_ADDR:
		# This packet is only differentiated by the profile_id being
		# the first 10 bytes of the data
		profile_id = data[0:10]

		if profile_id not in map_pids:
			# Do not recognize this profile_id
			# See if it has been added recently
			update_profile_state(mi)
			if profile_id not in map_pids:
				profile_id = 'unknown'

	elif dst_addr in map_dest_pid:
		profile_id = map_dest_pid[dst_addr]

	else:
		# Don't recognize this destination addr, check if there is a new one
		update_profile_state(mi)
		if dst_addr in map_dest_pid:
			profile_id = map_dest_pid[dst_addr]
		else:
			profile_id = 'unknown'


	# Send the packet to the queue
	amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
	                        body=pkt,
	                        routing_key=profile_id)



