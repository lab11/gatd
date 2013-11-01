import glob
import os
import sys
import traceback
import time
import struct
import socket
import threading
import SocketServer
import pika
import json
import struct

# Hostname to connect to for rabbitmq queue
HOSTNAME = "inductor.eecs.umich.edu"

STREAM_EXCHANGE = "streamer_exchange"
RECEIVE_EXCHANGE = "receive_exchange"

PROFILE = "7aiOPJapXF"

amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
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

	if pkt['type'] != 'coilcube_raw':
		return

	print(pkt)

	outpkt = {}
	outpkt['profile_id'] = pkt['profile_id']
	outpkt['public']     = pkt['public']
	outpkt['time']       = pkt['time']
	outpkt['ccid']       = pkt['ccid']
	outpkt['type']       = 'coilcube_freq'

	# Create a nicely formated ccid
	# ex: 00:11:22:33:44:55:66:77
	ccid = '{:0>16x}'.format(pkt['ccid'])
	outpkt['ccid_mac'] = ':'.join([ccid[i:i+2] for i in range(0, 16, 2)])

	# Calculate watts
	if pkt['ccid'] in coilcubes:
		last_data = coilcubes[pkt['ccid']]
		count_diff = byte_subtract(pkt['counter'], last_data[1]);
		time_diff = pkt['time'] - last_data[0]
		freq = float(count_diff) / (float(time_diff)/1000.0)
		freq = round(freq, 2)

		outpkt['freq'] = freq

	else:
		print("first sighting of this cc")
		coilcubes[pkt['ccid']] = [0]*3

	coilcubes[pkt['ccid']][0] = pkt['time']
	coilcubes[pkt['ccid']][1] = pkt['counter']
	coilcubes[pkt['ccid']][2] = pkt['seq_no']

	print(outpkt)

	ojson = json.dumps(outpkt)
	ojson = '\x02' + ojson

	amqp_chan.basic_publish(exchange=RECEIVE_EXCHANGE, body=ojson,
		routing_key='')



# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=STREAM_EXCHANGE,
	queue=strm_queue.method.queue, arguments=keys)
amqp_chan.basic_consume(process_packet,	queue=strm_queue.method.queue, no_ack=True)
amqp_chan.start_consuming()


