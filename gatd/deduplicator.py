
import argparse
import ipaddress
import pickle
import uuid

import arrow
import pika

import gatdBlock
import gatdLog

l = gatdLog.getLogger('dedup')


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
def check_packet (args, channel, method, prop, body):
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
	now = arrow.utcnow().timestamp
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
		# for target in routing_keys:
		channel.basic_publish(exchange='xch_scope_a',
		                      body=pickle.dumps(body),
		                      routing_key=str(args.uuid))

	# Ack all packets
	channel.basic_ack(delivery_tag=method.delivery_tag)


settings = [
	('time', int),
	('compare_addresses', str)
]
parameters = []


gatdBlock.start_block(l, 'Deduplicate', settings, parameters, check_packet)


