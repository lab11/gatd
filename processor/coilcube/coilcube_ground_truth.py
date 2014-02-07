#!/usr/bin/env python2

import json
import os
import pika
import struct
import sys

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

MON_PROFILE = '7aiOPJapXF'
WUP_PROFILE = 'YWUr2G8AZP'

amqp_conn = pika.BlockingConnection(
            	pika.ConnectionParameters(
            		host=gatdConfig.rabbitmq.HOST,
            		port=gatdConfig.rabbitmq.PORT,
            		credentials=pika.PlainCredentials(
            			gatdConfig.rabbitmq.USERNAME,
            			gatdConfig.rabbitmq.PASSWORD)
            	))
amqp_chan = amqp_conn.channel()


# Dict of ccid_mac -> wattsup data
wattsup = {}


# Called when each packet is received by this handler.
def process_packet (ch, method, properties, body):
	# Determine if the incoming packet matches the query from the client
	pkt = json.loads(body)

	if pkt['profile_id'] == WUP_PROFILE:
		if 'ccid_mac' in pkt:
			wattsup[pkt['ccid_mac']] = pkt

	elif pkt['profile_id'] == MON_PROFILE:
		if (not 'type' in pkt) or (pkt['type'] != 'coilcube_freq'):
			# Only operate on coilcube_freq packets
			return

		if pkt['ccid_mac'] in wattsup:
			newest_data = wattsup[pkt['ccid_mac']]
			pkt['ground_truth_watts'] = newest_data['watts']
			pkt['ground_truth_power_factor'] = newest_data['power factor']
			pkt['type'] = 'coilcube_freq_ground_truth'

			print(pkt)

			ojson = json.dumps(pkt)
			ojson = struct.pack('B', gatdConfig.pkt.TYPE_PROCESSED) + ojson

			amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
			                        body=ojson,
			                        routing_key='')



# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=gatdConfig.rabbitmq.XCH_STREAM,
                     queue=strm_queue.method.queue)
amqp_chan.basic_consume(process_packet,
                        queue=strm_queue.method.queue,
                        no_ack=True)
amqp_chan.start_consuming()
