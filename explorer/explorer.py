#!/usr/bin/env python2

import glob
import json
import os
import pika
import re
import struct
import sys
import setproctitle

sys.path.append(os.path.abspath('../config'))
import gatdConfig



search = {
			'U8H29zqH0i': [{
								'key': 'location_str',
								'children': [{
												'key': 'type',
												'children': []
											 }]
						   },
						   {
								'key': 'uniqname',
								'children': []
						   },
						   {
						   		'key': 'full_name',
						   		'children': []
						   }
						]
		}

data = {}


def data_recurse (data_struct, search_list, inpkt):

	# End when our search list is an empty list. This means there are no
	# more keys in our hierarchy
	if not search_list:
		return

	for s in search_list:
		k = s['key']

		if k in inpkt:

			if k not in data_struct:
				data_struct[k] = {}

			v = inpkt[k]

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

	#print(inpkt)

	pid = inpkt['profile_id']

	if pid in search:

		# Add the new profile_id to the data item if it is no there
		if pid not in data:
			data[pid] = {}

		searches = search[pid]

		data_recurse(data[pid], searches, inpkt)


		print(data)









setproctitle.setproctitle('gatd-explore')

amqp_conn = pika.BlockingConnection(
            	pika.ConnectionParameters(
            	host=gatdConfig.rabbitmq.HOST,
            	port=gatdConfig.rabbitmq.PORT,
            	credentials=pika.PlainCredentials(
            		gatdConfig.rabbitmq.USERNAME,
            		gatdConfig.rabbitmq.PASSWORD)))
amqp_chan = amqp_conn.channel()

# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=gatdConfig.rabbitmq.XCH_STREAM,
                     queue=strm_queue.method.queue)
amqp_chan.basic_consume(got_packet,
                        queue=strm_queue.method.queue,
                        no_ack=True)
amqp_chan.start_consuming()
