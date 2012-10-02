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

RMQ_HOST    = 'inductor.eecs.umich.edu'
RMQ_QUEUE   = 'receive_queue'
RMQ_STR_EXC = 'streamer_exchange'

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

	type = struct.unpack('B', pkt[0:1])[0]
	pkt  = pkt[1:]

	if type == PKT_TYPE_UDP or type == PKT_TYPE_TCP:
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



mi = MongoInterface.MongoInterface(host=MONGO_HOST, port=MONGO_PORT)
pm = profileManager.profileManager(mi)
ac = archiveCleaner.archiveCleaner(db=mi, pm=pm)
ri = RabbitInterface.RabbitInterface(host=RMQ_HOST)

# Read in all config files
for root, dirs, files in os.walk('.'):
	for f in files:
		name, ext = os.path.splitext(f)
		if ext == '.config':
			pm.addConfigFile(root + '/' + f)


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

		# Send to streamer
		ri.publish(exchange=RMQ_STR_EXC, body=jsonv)


	except FE.ParserNotFound as e:
		print "unknown"
		print data
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
	ri.ack(method.delivery_tag)


ri.consume(packet_callback, queue=RMQ_QUEUE, no_ack=False)

