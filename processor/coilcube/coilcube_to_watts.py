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

profile = "7aiOPJapXF"

amqp_conn = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
amqp_chan = amqp_conn.channel()

keys = {}
keys['profile_id'] = profile
keys['x-match'] = "all"

# Dict to keep track of the last values of different coilcubes
# ccid -> [timestamp, count, seq_no, wattage]
coilcubes = {}

# Dict to hold calibration values
# ccid -> {freq -> watts}
calibration = {}

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

	wattpkt = {}
	wattpkt['profile_id'] = pkt['profile_id']
	wattpkt['public']     = pkt['public']
	wattpkt['time']       = pkt['time']
	wattpkt['ccid']       = pkt['ccid']
	wattpkt['type']       = 'coilcube_watts'

	# Create a nicely formated ccid
	# ex: 00:11:22:33:44:55:66:77
	ccid = '{:0>16x}'.format(pkt['ccid'])
	wattpkt['ccid_mac'] = ':'.join([ccid[i:i+2] for i in range(0, 16, 2)])

	# Calculate watts
	if pkt['ccid'] in coilcubes:
		last_data = coilcubes[pkt['ccid']]
		count_diff = byte_subtract(pkt['counter'], last_data[1]);
		time_diff = pkt['time'] - last_data[0]
		freq = float(count_diff) / (float(time_diff)/1000.0)
		freq = round(freq, 2)

		try:
			watts = calibration[pkt['ccid']][str(freq)]
			wattpkt['watts'] = watts
		except KeyError:
			print("Could not determine wattage for this frequency.")
			print("    ccid={}, ccid_mac={}, freq={}".format(pkt['ccid'], wattpkt['ccid_mac'], freq))
			return
	else:
		print("first sighting of this cc")
		coilcubes[pkt['ccid']] = [0]*4
	
	coilcubes[pkt['ccid']][0] = pkt['time']
	coilcubes[pkt['ccid']][1] = pkt['counter']
	coilcubes[pkt['ccid']][2] = pkt['seq_no']
	coilcubes[pkt['ccid']][3] = wattpkt.setdefault('watts', 0)

	wattjson = json.dumps(wattpkt)
	wattjson = '\x02' + wattjson

	amqp_chan.basic_publish(exchange=RECEIVE_EXCHANGE, body=wattjson,
		routing_key='')


# Load all of the calibration data
calib_files = glob.glob("calibration/*.json")
for fname in calib_files:
	with open(fname, 'r') as f:
		ccid = int(os.path.basename(fname).split('.')[0], 16)
		data = json.loads(f.read())
		calibration[ccid] = data


# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=STREAM_EXCHANGE,
	queue=strm_queue.method.queue, arguments=keys)
amqp_chan.basic_consume(process_packet,	queue=strm_queue.method.queue, no_ack=True)
amqp_chan.start_consuming()


