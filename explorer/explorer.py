#!/usr/bin/env python2

import glob
import json
import os
import pika
import re
import struct
import sys
import setproctitle

import pprint

sys.path.append(os.path.abspath('../config'))
sys.path.append(os.path.abspath('../formatter'))
import gatdConfig
import MongoInterface



search = {}

data = {}

pp = pprint.PrettyPrinter(indent=4)

# Recurse over the search data structure looking for matching keys in the
# incoming packet. Update the data_struct with the relevant information
def data_recurse (data_struct, search_list, inpkt):

	# End when our search list is an empty list. This means there are no
	# more keys in our hierarchy
	if not search_list:
		return

	for s in search_list:
		k = s['key']

		if k in inpkt:

			# If we haven't found this key yet make a note of it
			if k not in data_struct:
				data_struct[k] = {}

			v = inpkt[k]

			# If we haven't found this particular value of the key in question
			# make a note of it
			if v not in data_struct[k]:
				data_struct[k][v] = {}

			data_recurse(data_struct[k][v], s['children'], inpkt)



# Function called on each incoming packet from the channel
def got_packet (ch, method, prop, body):
	global amqp_chan

	try:
		inpkt = json.loads(body)
	except Exception as e:
		print('Could not parse JSON packet')
		print(e)

	pid = inpkt['profile_id']

	# Only bother to do anything with this packet if we have a explorer layout
	# for this profile
	if pid in search:

		# Add the new profile_id to the data item if it is not there
		if pid not in data:
			data[pid] = {}

		# Recursively iterate over the keys we are looking for to discover the
		# streams available
		data_recurse(data[pid], search[pid], inpkt)

		pp.pprint(data)







setproctitle.setproctitle('gatd-explore')

amqp_conn = pika.BlockingConnection(
            	pika.ConnectionParameters(
            	host=gatdConfig.rabbitmq.HOST,
            	port=gatdConfig.rabbitmq.PORT,
            	credentials=pika.PlainCredentials(
            		gatdConfig.rabbitmq.USERNAME,
            		gatdConfig.rabbitmq.PASSWORD)))
amqp_chan = amqp_conn.channel()

mi = MongoInterface.MongoInterface()
dbdata = mi.getExploreKeys()
for pidkeys in dbdata:
	search[pidkeys['profile_id']] = json.loads(pidkeys['keys_json'])

# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=gatdConfig.rabbitmq.XCH_STREAM,
                     queue=strm_queue.method.queue)
amqp_chan.basic_consume(got_packet,
                        queue=strm_queue.method.queue,
                        no_ack=True)
amqp_chan.start_consuming()
