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


amqp_chan = None

# Function called on each incoming packet from the channel
def run_processor (processor_func, processor_idname, pkt_body):
	global amqp_chan

	try:
		inpkt = json.loads(pkt_body)
	except Exception as e:
		print('Could not parse JSON packet')
		print(e)

	try:
		pkt = processor_func(inpkt)
	except Exception:
		# Any exception the processor returns just ignore
		print('exc')
		return

	if pkt == None:
		# The processor did not return a packet either out of an error
		# or because it didnt' want to
		return

	if type(pkt) != dict:
		# Not a dict, that is incorrect
		return

	if 'profile_id' not in pkt:
		# All packets MUST have a profile id. This is an error.
		return

	# Update the processor history of this packet
	# Scan through to find the previous processors and which one was marked
	# as last
	proc_last = ''
	for key in pkt.keys():
		if key[0:10] == '_processor':
			# one of the special keys
			if pkt[key] == 'last':
				proc_last = key

	count = pkt['_processor_count']

	# Convert the last processor to the second to last
	if proc_last != '':
		pkt[proc_last] = count - 1

	# Mark this as the last processor
	pkt['_processor_' + processor_idname] = 'last'
	pkt['_processor_count'] = count + 1

	# Send packet back into gatd
	ojson = struct.pack('B', gatdConfig.pkt.TYPE_PROCESSED) + json.dumps(pkt)

	amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
	                        body=ojson,
	                        routing_key='')



if len(sys.argv) != 2:
	print('ERROR: Must specify the processor to run as the first argument.')
	sys.exit(1)

processor_name = sys.argv[1]

setproctitle.setproctitle('gatd-p: ' + processor_name)

__import__('processors.'+processor_name)
processor_mod = sys.modules['processors.{}'.format(processor_name)]
processor_n = getattr(processor_mod, processor_name)
# Create a processor instance to run on packets
processor = processor_n()

try:
	idname = processor.idname
except Exception:
	print('ERROR: no idname found for processor {}'.format(processor_name))
	sys.exit(1)

# Verify that the id name is only letters and underscores
if re.match('^[a-zA-Z_]*$', idname) == None:
	print('ERROR: idname for processor {} contains invalid characters.'
		.format(processor_name))
	print('ERROR:   only use letters and underscores')
	sys.exit(1)

try:
	query = processor.query
except Exception:
	print('ERROR: no query found for processor {}'.format(processor_name))
	sys.exit(1)


cb = lambda ch, method, prop, body: run_processor(processor.process,
                                                  idname,
                                                  body)

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
                     queue=strm_queue.method.queue,
                     arguments=query)
amqp_chan.basic_consume(cb,
                        queue=strm_queue.method.queue,
                        no_ack=True)
amqp_chan.start_consuming()
