import bson.binary
import IPy
import json
import os
import pika
import struct
import sys

import archiveCleaner
import Deduplicator
import FormatterExceptions as FE
sys.path.append(os.path.abspath('../config'))
import gatdConfig
import MongoInterface
import profileManager


# Unpack the packet from the receiver/querier
# Returns tuple(data string, meta info dict)
# Throws BadPacket if something is wrong
def unpackPacket (pkt):
	if len(pkt) < 2:
		# Packet can't have any payload, discard it
		raise FE.BadPacket('Packet too short. No payload.')

	ptype = struct.unpack('B', pkt[0:1])[0]
	pkt   = pkt[1:]

	if ptype in [gatdConfig.pkt.TYPE_UDP,
	             gatdConfig.pkt.TYPE_TCP,
	             gatdConfig.pkt.TYPE_HTTP_POST]:
		if len(pkt) < gatdConfig.pkt.HEADER_LEN:
			raise FE.BadPacket('Packet header too short.')

		record  = struct.unpack('>QQHQ', pkt[0:gatdConfig.pkt.HEADER_LEN])
		addr    = int('0x{:0>16x}{:0>16x}'.format(*record[0:2]), 16)
		laddr   = int('0x{:0>16x}'.format(record[1]), 16)
		port    = record[2]
		time    = record[3]
		if len(pkt) > gatdConfig.pkt.HEADER_LEN:
			data = struct.unpack('>%is' % (len(pkt)-gatdConfig.pkt.HEADER_LEN),
			                     pkt[gatdConfig.pkt.HEADER_LEN:])[0]
		else:
			data = ''

		# Check if the packet is a duplicate
		duplicate = dd.check(port=port, addr=laddr, data=data, time=time)
		if duplicate:
			return None

		meta = {}
		meta['addr'] = addr
		meta['port'] = port
		meta['time'] = time

		return (data, meta)

	elif ptype == gatdConfig.pkt.TYPE_PROCESSED:
		try:
			data = json.loads(pkt)

			if 'profile_id' not in data:
				raise FE.BadPacket('"profile_id" key must be in processed data \
json blob')

			return (data, None)

		except ValueError as e:
			raise FE.BadPacket("Processed packet not JSON.")
	else:
		raise FE.BadPacket('Invalid type of packet')

	return None

# Called each time a packet comes in from the RabbitMQ queue
def packet_callback (channel, method, prop, body):

	try:
		# Parse out the fields from the receiver
		data, meta = unpackPacket(body)

		if meta == None:
			# This is a processed packet that has already been through
			# the system once. It does not need to be formatted.
			ret = data

		else:
			# Process the packet by the correct parser
			ret = pm.parsePacket(data=data, meta=meta)
			if ret == None:
				# Discard this packet from storage and the streamer
				raise Exception

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
		channel.basic_publish(exchange=gatdConfig.rabbitmq.XCH_STREAM,
		                      body=jsonv,
		                      properties=props,
							  routing_key='')


	except FE.ParserNotFound as e:
		print "No parser found for the incoming message."
		print "Len:  {}".format(len(data))
		print "Data: {}".format(data[0:10])
		print "Addr: {}".format(IPy.IP(meta['addr']))
		print "Port: {}".format(meta['port'])
		print "Time: {}".format(meta['time'])
		# archive
		meta['addr'] = str(meta['addr'])
		mi.writeUnformatted({'meta': meta,
			                 'data': bson.binary.Binary(body[26:], 0)})

	except FE.BadPacket as e:
		print "BadPacket: " + str(e)

	except FE.ParserError as e:
		print "ParseError: " + str(e)

	except UnicodeDecodeError as e:
		print(e)
		pass

	except Exception as e:
		print(e)
		pass

	except TypeError:
		# Invalid incoming packet so the unpacker returned None
		pass

	# Ack the packet from the receiver so rabbitmq doesn't try to re-send it
	channel.basic_ack(delivery_tag=method.delivery_tag)

dd = Deduplicator.Deduplicator()
mi = MongoInterface.MongoInterface()
pm = profileManager.profileManager(mi)
ac = archiveCleaner.archiveCleaner(db=mi, pm=pm)

connection = pika.BlockingConnection(
				pika.ConnectionParameters(host=gatdConfig.rabbitmq.HOST))
channel = connection.channel()

# Create the exchange for the streaming packets.
# Let the queues be created by the streamers. If there are no streamers
# running, then the messages will just be dropped and that is OK.
channel.exchange_declare(exchange=gatdConfig.rabbitmq.XCH_STREAM,
                         exchange_type='headers',
                         durable=True)

# Read in all config files
for root, dirs, files in os.walk('./configs'):
	for f in files:
		name, ext = os.path.splitext(f)
		if ext == '.config':
			pm.addConfigFile(root + '/' + f)

channel.basic_consume(packet_callback,
                      queue=gatdConfig.rabbitmq.Q_RECEIVE,
                      no_ack=False)
channel.start_consuming()

