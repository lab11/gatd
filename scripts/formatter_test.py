#!/usr/bin/env python2

import argparse
import base64
import bson.binary
import IPy
import json
import os
import pika
import pprint
import struct
import sys


sys.path.append(os.path.abspath('../config'))
sys.path.insert(0, os.path.abspath('../formatter'))
import FormatterExceptions as FE
import gatdConfig
import MongoInterface
import profileManager

import logging
logging.basicConfig()


info = """Use this tool to test your formatter before committing it to
GATD proper.
"""


# Basically use the profileManager class that already exists, except
# do not load all the other parsers in
class profileTester (profileManager.profileManager):

	def __init__ (self, db, parser_file, profile_id):

		self.db = db

		sys.path.append(os.path.dirname(parser_file))
		self._loadParserFile(parser_file)

		# Verify that everything went well
		if profile_id not in self.configs:
			print('loading parser {} failed.'.format(parser_file))
			print('Double check the parser has a class the same as')
			print('the filename and the profile_id is correct')
			sys.exit(1)



# Class for handling all of the pika connection things
class PikaConnection (object):

	def __init__(self, packet_callback):

		self._connection = None
		self._channel = None
		self._cb = packet_callback

	def connect(self):
		return pika.SelectConnection(
			pika.ConnectionParameters(
				host=gatdConfig.rabbitmq.HOST,
				port=gatdConfig.rabbitmq.PORT,
				credentials=pika.PlainCredentials(
					gatdConfig.rabbitmq.USERNAME,
					gatdConfig.rabbitmq.PASSWORD)),
			self.on_connection_open)

	def on_connection_open(self, unused_connection):
		self._connection.channel(on_open_callback=self.on_channel_open)

	def on_channel_open(self, channel):
		self._channel = channel
		self._channel.queue_declare(self.on_queue_declareok,
		                            exclusive=True,
		                            auto_delete=True)

	def on_queue_declareok(self, method_frame):
		self._queue = method_frame.method.queue
		self._channel.queue_bind(self.on_bindok,
		                         exchange=gatdConfig.rabbitmq.XCH_FORMATTER_TEST,
		                         queue=self._queue)

	def on_bindok(self, unused_frame):
		self._channel.basic_consume(self._cb,
	                                queue=self._queue,
	                                no_ack=True)

	def run(self):
		self._connection = self.connect()
		self._connection.ioloop.start()

	def stop(self):
		self.stop_consuming()
		self._connection.ioloop.start()




# Called each time a packet comes in from the RabbitMQ queue
def packet_callback (channel, method, prop, body):

	try:
		pkt = json.loads(body)

		data = base64.b64decode(pkt['data'])
		
		# Process the packet by the correct parser
		ret = pt.parsePacket(data=data, meta=pkt['meta'])
		if ret == None:
			# Discard this packet from storage and the streamer
			raise Exception

		print('Received:')
		print(data)
		print('as the raw input.')
		print('')

		print('After formatting got:')
		pp.pprint(ret)
		print('')
		print('')
		print('')



	except FE.ParserNotFound as e:
		# ignore
		pass

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



parser = argparse.ArgumentParser(description=info)
parser.add_argument('--parser_file',
                    required=True,
                    help='path to parser file')
parser.add_argument('--profile_id',
                    required=True,
                    help='10 character profile id')

args = parser.parse_args()

class HexAndIntPrettyPrinter(pprint.PrettyPrinter):
	def format(self, object, context, maxlevels, level):
		repr, readable, recursive = pprint.PrettyPrinter.format(
				self, object, context, maxlevels, level)
		if isinstance(object, int):
			return "{} (0x{:x})".format(object, object), readable, recursive
		else:
			return repr, readable, recursive

pp = HexAndIntPrettyPrinter()
mi = MongoInterface.MongoInterface()
pt = profileTester(mi, args.parser_file, args.profile_id)
pi = PikaConnection(packet_callback)
pi.run()
