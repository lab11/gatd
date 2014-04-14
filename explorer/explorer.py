#!/usr/bin/env python2

import glob
import json
import os
import pika
import setproctitle
import sys
import tornado.ioloop
import tornado.web

import pprint

sys.path.append(os.path.abspath('../config'))
sys.path.append(os.path.abspath('../formatter'))
import gatdConfig
import MongoInterface


search = {}

data = {}



# Recurse over the search data structure looking for matching keys in the
# incoming packet. Update the data_struct with the relevant information
def data_recurse (data_struct, search_list, inpkt):

	# End when our search list is an empty list. This means there are no
	# more keys in our hierarchy
	if not search_list:
		return

	for s in search_list:
		k = s['key']

		if k in inpkt:

			# If we haven't found this key yet make a note of it
			if k not in data_struct:
				data_struct[k] = {}

			v = inpkt[k]

			# If we haven't found this particular value of the key in question
			# make a note of it
			if v not in data_struct[k]:
				data_struct[k][v] = {}

			data_recurse(data_struct[k][v], s['children'], inpkt)


# Class for handling all of the pika connection things
class PikaConnection (object):

	def __init__(self):

		self._connection = None
		self._channel = None
		self._closing = False
		self._consumer_tag = None

	def connect(self):
		return pika.adapters.TornadoConnection(
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
		                         exchange=gatdConfig.rabbitmq.XCH_STREAM,
		                         queue=self._queue)

	def on_bindok(self, unused_frame):
		self._channel.basic_consume(self.got_packet,
	                                queue=self._queue,
	                                no_ack=True)



	def run(self):
		self._connection = self.connect()
		#self._connection.ioloop.start()

	def stop(self):
		self._closing = True
		self.stop_consuming()
		self._connection.ioloop.start()


	# Function called on each incoming packet from the channel
	def got_packet (self, ch, method, prop, body):

		try:
			inpkt = json.loads(body)
		except Exception as e:
			print('Could not parse JSON packet')
			print(e)

		pid = inpkt['profile_id']

		# Only bother to do anything with this packet if we have a explorer layout
		# for this profile
		if pid in search:

			# Add the new profile_id to the data item if it is not there
			if pid not in data:
				data[pid] = {}

			# Recursively iterate over the keys we are looking for to discover the
			# streams available
			data_recurse(data[pid], search[pid], inpkt)

			#pp.pprint(data)
			#print('packet')


# Class for handling the message that says the explore keys were updated
class ExploreKeysUpdateHandler (tornado.web.RequestHandler):
	def post (self, pid):

		# Get the keys for this profile id
		dbkeys = mi.getExploreKeysSingle(pid)

		# Remove the old configuration and data
		if pid in search:
			del search[pid]

		if pid in data:
			del data[pid]

		# Add a new search for the given profile
		search[pid] = json.loads(dbkeys['keys_json'])

		print('Updated {}'.format(pid))

class ExploreKeysBaseHandler (tornado.web.RequestHandler):
	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")

class ExploreKeysAllHandler (ExploreKeysBaseHandler):
	def get (self):
		self.set_header('Content-Type', 'application/json')


		meta = {}
		configs = mi.getAllConfigs()
		for config in configs:
			if config['profile_id'] in data:
				meta[config['profile_id']] = {}
				for k,v in config.items():
					if k not in ['profild_id', '_id']:
						meta[config['profile_id']][k] = v

		out = {
				'meta': meta,
				'explore': data
		}

		self.write(json.dumps(out))

class ExploreKeysRequestHandler (ExploreKeysBaseHandler):
	def get (self, pid):
		self.set_header('Content-Type', 'application/json')
		if pid in data:
			self.write(json.dumps(data[pid]))
		else:
			self.write('{}')

class ExploreKeysNameHandler (ExploreKeysBaseHandler):
	def get (self, pid):
		self.set_header('Content-Type', 'application/json')
		dbdata = mi.getConfigByProfileId(pid)

		if dbdata:
			self.write(json.dumps({'profile_id': pid,
			                       'name':       dbdata['parser_name']}))
		else:
			self.write('{}')



# Make this python instance recognizable in top
setproctitle.setproctitle('gatd-explore')

# Connect to mongo
mi = MongoInterface.MongoInterface()

# Do the initial load of all the keys we are searching for
dbdata = mi.getExploreKeys()
for pidkeys in dbdata:
	search[pidkeys['profile_id']] = json.loads(pidkeys['keys_json'])


pp = pprint.PrettyPrinter(indent=4)

p = PikaConnection()

t = tornado.web.Application([
	(r"/explore/update/(.*)", ExploreKeysUpdateHandler),
	(r"/explore/all", ExploreKeysAllHandler),
	(r"/explore/profile/([a-zA-Z0-9]*)", ExploreKeysRequestHandler),
	(r"/explore/profile/name/([a-zA-Z0-9]*)", ExploreKeysNameHandler),
])

p.run()
t.listen(gatdConfig.explorer.PORT_HTTP_POST)



# Run the loop!
# This works for both tornado and pika/rabbitmq
tornado.ioloop.IOLoop.instance().start()



