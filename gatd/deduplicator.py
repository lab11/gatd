
import argparse
import ipaddress
import uuid

import arrow
import pika
import setproctitle

import gatdBlock
import gatdLog

l = gatdLog.getLogger('dedup')

setproctitle.setproctitle('gatd:dedup')

#
# Returns true if the packet is unique, false if it is a duplicate
#
# Each packet is in a hash table with its timestamp. If another packet
# comes in with the same data and a very similar timestamp it is considered
# a duplicate.
# In any case the packet is added with its timestamp


# dict of packet -> timestamp
packet_hashes = {}

# array of timestamps
timestamps = []

# dict of timestamp -> packet
time_hashes = {}


#
# Deduplicator works on scope 'a' packets. That means they look like this:
#
# {
# 	'src_addr':     <ip address> (optional)
# 	'src_port':     <port num>   (optional)
# 	'time_utc_iso': <time str>
# 	'data':         <data blob> OR <{'body': <data blob>, 'headers': <headers>}>
# }
#

# Call this function on the incoming data message to check if it is
# a duplicate or not
def check_packet (channel, method, prop, body):
#def check_packet (self, port, addr, data, time):

	duplicate = False

	# Check if we should look at part of the IP address too
	if 'src_addr' in body and args.compare_addresses == 'true':
		ip = ipaddress.ip_address(data['src_addr'])
		addr = ip.exploded[20:]
	else:
		addr = ''

	#key = '{}{}{}'.format(port, addr, data)
	key  = (body['data'], addr)

	# Get the time of the packet in seconds
	time = arrow.get(body['time_utc_iso']).timestamp

	# Retrieve the last time this data was seen, or 0 if this is the first
	# time
	previous_time = packet_hashes.setdefault(key, 0)

	if previous_time > 0:
		if abs(time - previous_time) < args.time:
			duplicate = True

	# Put this packet in the dict for the next go around
	packet_hashes[key] = time

	# Save the timestamp and backwards lookup
	timestamps.append(time)
	time_hashes[time] = key

	# Get rid of old packets from the dicts to reduce memory usage
	now = arrow.utcnow.timestamp
	while True:
		if len(timestamps) == 0:
			break

		time_check = timestamps[0]
		if now - time_check > args.time:
			# Deleting this timestamp
			timestamps.pop(0)

			# Get the packet that corresponds to that time
			pkt = time_hashes[time_check]

			# Get the timestamp that that packet came in at
			saved_time = packet_hashes[pkt]

			# Check that a newer duplicate packet didn't come in and
			# update the timestamp
			if saved_time == time_check:
				# Go ahead and delete the packet
				del packet_hashes[pkt]
				del time_hashes[time_check]

		else:
			break


	if not duplicate:
		for target in routing_keys:
			channel.basic_publish(exchange='xch_deduplicator',
			                      body=body,
			                      routing_key=target)

	# Ack all packets
	channel.basic_ack(delivery_tag=method.delivery_tag)


settings = [
	('time', int),
	('compare_addresses', str)
]
parameters = []

# Global arguments
args = None
routing_keys = None

gatdBlock.start_block(l, 'Deduplicate', settings, parameters, check_packet)

# parser = argparse.ArgumentParser(description='Deduplicate')
# parser.add_argument('--uuid',
#                     type=uuid.UUID,
#                     nargs=1,
#                     required=True)
# parser.add_argument('--time',
#                     type=int,
#                     nargs=1,
#                     required=True)
# parser.add_argument('--compare_addresses',
#                     nargs=1,
#                     required=True)
# parser.add_argument('--source_uuid',
#                     nargs='+',
#                     type=uuid.UUID)
# parser.add_argument('--target_uuid',
#                     nargs='+',
#                     type=uuid.UUID)

# args = parser.parse_args()

# # Pre-enumerate all of the routing keys that we send packets to
# routing_keys = []
# for target in args.target_uuid:
# 	routing_keys.append('{}_{}'.format(args.uuid, str(target)))

# # Setup the connection to RabbitMQ
# def pika_on_channel (amqp_chan):

# 	for src in args.source_uuid:
# 		queue_name = '{}_{}'.format(str(src), str(args.uuid))

# 		l.info('Deduplicating packets from queue {}'.format(queue_name))

# 		amqp_chan.basic_consume(check_packet,
# 		                        queue=queue_name,
# 		                        no_ack=False)

# def pika_on_connection (unused_connection):
# 	amqp_conn.channel(pika_on_channel)

# amqp_conn = pika.SelectConnection(
# 				pika.ConnectionParameters(
# 					host=gatdConfig.rabbitmq.HOST,
# 					port=gatdConfig.rabbitmq.PORT,
# 					credentials=pika.PlainCredentials(
# 						gatdConfig.deduplicator.RMQ_USERNAME,
# 						gatdConfig.deduplicator.RMQ_PASSWORD)),
# 				pika_on_connection
# 			)
# amqp_conn.ioloop.start()

