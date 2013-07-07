import archiveCleaner
import bson.binary
import FormatterExceptions as FE
import IPy
import json
import MongoInterface
import os
import profileManager
import pika
import RabbitInterface
import struct
import sys

RMQ_HOST        = 'inductor.eecs.umich.edu'
RECEIVE_QUEUE   = 'receive_queue'
STREAM_EXCHANGE = 'streamer_exchange'

MONGO_HOST  = 'inductor.eecs.umich.edu'
MONGO_PORT  = 19000

PKT_TYPE_UDP       = 0
PKT_TYPE_TCP       = 1

PKT_HEADER_LEN_UDP = 26
PKT_HEADER_LEN_TCP = 26

# Unpack the packet from the receiver/querier
# Returns tuple(data string, meta info dict)
# Throws BadPacket if something is wrong
def unpackPacket (pkt):
	if len(pkt) < 2:
		# Packet can't have any payload, discard it
		raise FE.BadPacket('Packet too short. No payload.')

	ptype = struct.unpack('B', pkt[0:1])[0]
	pkt   = pkt[1:]

	if ptype == PKT_TYPE_UDP or ptype == PKT_TYPE_TCP:
		if len(pkt) < PKT_HEADER_LEN_UDP:
			raise FE.BadPacket('Malformed udp/tcp packet.')

		record  = struct.unpack('>4IHQ', pkt[0:PKT_HEADER_LEN_UDP])
		addr    = int('0x%x%x%x%x' % tuple(record[0:4]), 16)
		port    = record[4]
		time    = record[5]
		if len(pkt) > PKT_HEADER_LEN_UDP:
			data = struct.unpack('>%is' % (len(pkt)-PKT_HEADER_LEN_UDP),
			                     pkt[PKT_HEADER_LEN_UDP:])[0]
		else:
			data = ''

		meta = {}
		meta['addr'] = addr
		meta['port'] = port
		meta['time'] = time

		return (data, meta)

	else:
		raise FE.BadPacket('Invalid type of packet')

	return None


def packet_callback (channel, method, prop, body):

	try:

		# Parse out the fields from the receiver
		data, meta = unpackPacket(body)

		# Process the packet by the correct parser
		ret = pm.parsePacket(data=data, meta=meta)

		# Convert dict to nice json thingy
		jsonv = json.dumps(ret)

		# Save in database
		mi.writeFormatted(ret)

		# Set the headers to the keys present in the streamed message
		# The headers are key, value pairs where the keys are the same keys as
		# in the packet and the values are a single NULL byte. The only
		# exception is the "profile_id" key, which is set to the profile id
		# string because it is included in ALL packets. This allows for
		# efficient handling of a common use case, which is to receive all
		# packets from a specific profile.
		headers = dict((x,struct.pack('B',0)) for x in ret.keys())
		headers['profile_id'] = ret['profile_id']
		props = pika.spec.BasicProperties(headers=headers)

		# Send to streamer
		channel.basic_publish(exchange=STREAM_EXCHANGE, body=jsonv,
		                      properties=props, routing_key='')


	except FE.ParserNotFound as e:
		print "No parser found for the incoming message."
		print "Data: {}".format(data)
		print "Addr: {}".format(IPy.IP(meta['addr']))
		print "Port: {}".format(meta['port'])
		print "Time: {}".format(meta['time'])
		# archive
		mi.writeUnformatted({'meta': meta,
			                 'data': bson.binary.Binary(body[26:], 0)})

	except FE.BadPacket as e:
		print "BadPacket: " + str(e)

	except FE.ParserError as e:
		print "ParseError: " + str(e)

	except UnicodeDecodeError:
		pass

	# Ack the packet from the receiver so rabbitmq doesn't try to re-send it
	channel.basic_ack(delivery_tag=method.delivery_tag)	


mi = MongoInterface.MongoInterface(host=MONGO_HOST, port=MONGO_PORT)
pm = profileManager.profileManager(mi)
ac = archiveCleaner.archiveCleaner(db=mi, pm=pm)

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST))
channel = connection.channel()

# Create the exchange for the streaming packets.
# Let the queues be created by the streamers. If there are no streamers
# running, then the messages will just be dropped and that is OK.
channel.exchange_declare(exchange=STREAM_EXCHANGE, exchange_type='headers',
                         durable=True)

# Read in all config files
for root, dirs, files in os.walk('.'):
	for f in files:
		name, ext = os.path.splitext(f)
		if ext == '.config':
			pm.addConfigFile(root + '/' + f)

channel.basic_consume(packet_callback, queue=RECEIVE_QUEUE, no_ack=False)
channel.start_consuming()

