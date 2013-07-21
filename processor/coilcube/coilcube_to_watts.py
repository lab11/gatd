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
	wattpkt['watts']      = pkt['counter']

	ccid = '{:0>16x}'.format(pkt['ccid'])
	wattpkt['ccid_mac'] = ':'.join([ccid[i:i+2] for i in range(0, 16, 2)])

	wattjson = json.dumps(wattpkt)
	wattjson = '\x02' + wattjson
	print wattjson

	amqp_chan.basic_publish(exchange=RECEIVE_EXCHANGE, body=wattjson,
		routing_key='')


# Setup a queue to get the necessary stream
strm_queue = amqp_chan.queue_declare(exclusive=True, auto_delete=True)
amqp_chan.queue_bind(exchange=STREAM_EXCHANGE,
	queue=strm_queue.method.queue, arguments=keys)
amqp_chan.basic_consume(process_packet,	queue=strm_queue.method.queue, no_ack=True)
amqp_chan.start_consuming()


