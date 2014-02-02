import json
import os
import pika
import struct
import sys

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

PROFILE = "7aiOPJapXF"

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
keys['profile_id'] = PROFILE
keys['x-match'] = "all"

# Dict to keep track of the last values of different coilcubes
# ccid -> [timestamp, count, seq_no]
coilcubes = {}

def byte_subtract (a, b):
	if (a >= b):
		return a-b
	else:
		return a + (256-b)

# Called when each packet is received by this handler.
def process_packet (ch, method, properties, body):
	# Determine if the incoming packet matches the query from the client
	pkt = json.loads(body)

	if 'type' not in pkt or pkt['type'] != 'coilcube_raw':
		return

	# Make sure the keys we need are in the packet
	if 'ccid' not in pkt or
	   'ccid_mac' not in pkt or
	   'counter' not in pkt or
	   'seq_no' not in pkt:
		return

	# Change the type
	pkt['type'] = 'coilcube_freq'

	# Calculate the frequency
	if pkt['ccid'] in coilcubes:
		last_data  = coilcubes[pkt['ccid']]
		count_diff = byte_subtract(pkt['counter'], last_data[1]);
		time_diff  = pkt['time'] - last_data[0]
		if time_diff == 0:
			return
		freq = float(count_diff) / (float(time_diff)/1000.0)
		freq = round(freq, 4)

		pkt['freq'] = freq

	else:
		print("first sighting of this cc: {}".format(pkt['ccid_mac']))
		coilcubes[pkt['ccid']] = [0]*3

	coilcubes[pkt['ccid']][0] = pkt['time']
	coilcubes[pkt['ccid']][1] = pkt['counter']
	coilcubes[pkt['ccid']][2] = pkt['seq_no']

	# Now remove the seq no and counter
	del pkt['counter']
	del pkt['seq_no']

	ojson = json.dumps(pkt)
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

