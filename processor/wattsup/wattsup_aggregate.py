#!/usr/bin/env python2
import json
import os
import pika
import struct
import sys

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

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

keys = {}
keys['profile_id'] = WUP_PROFILE
keys['x-match'] = "all"

# dict of location->{wattsupid->watts}
wattsups = {}


# Called when each packet is received by this handler.
def process_packet (ch, method, properties, body):
	# Determine if the incoming packet matches the query from the client
	pkt = json.loads(body)

	if 'type' in pkt:
		# Only want unprocessed packets
		return

	# Make sure the keys we need are in the packet
	if 'location_str' not in pkt or \
	   'watts' not in pkt:
		return

	opkt = {}
	opkt['type'] = 'local_aggregate'
	opkt['time'] = pkt['time']
	opkt['public'] = pkt['public']
	opkt['profile_id'] = pkt['profile_id']

	location_fields = pkt['location_str'].split('|')
	agg_location = '|'.join(location_fields[0:-1])
	opkt['location_str'] = agg_location
	opkt['description'] = 'Aggregate from Watts Up? at {}' \
		.format(', '.join(location_fields[0:-1]))

	location_watts = wattsups.setdefault(agg_location, {})
	location_watts[pkt['wattsupid']] = pkt['watts']

	total = 0.0
	for watt in location_watts.itervalues():
		total += watt
	opkt['watts'] = total

	print(opkt)

	ojson = json.dumps(opkt)
	ojson = struct.pack('B', gatdConfig.pkt.TYPE_PROCESSED) + ojson

	amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
	                        body=ojson,
	                        routing_key='')



# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=gatdConfig.rabbitmq.XCH_STREAM,
                     queue=strm_queue.method.queue,
                     arguments=keys)
amqp_chan.basic_consume(process_packet,
                        queue=strm_queue.method.queue,
                        no_ack=True)
amqp_chan.start_consuming()
