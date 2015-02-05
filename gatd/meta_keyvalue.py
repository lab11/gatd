
"""
Add key-value pairs to a data packet if the packet contains a particular
key-value pair.
"""

import copy
import pickle

import pymongo

import gatdBlock
import gatdConfig
import gatdLog

l = gatdLog.getLogger('meta-keyvalue')

queries = {}
additional = {}

def connect_mongodb ():
	# get a mongo connection
	mc = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                         port=gatdConfig.mongo.PORT)
	mdb = mc['gatdv6']
	mdb.authenticate(gatdConfig.blocks.MDB_USERNAME,
	                 gatdConfig.blocks.MDB_PASSWORD)

	return mdb


def process (args, channel, method, prop, body):
	data = copy.deepcopy(body)

	for k,v in body.items():
		if k[0] != '_':
			if k in queries:
				if queries[k] == v:
					for add in additional[k][v]:
						data[add[0]] = add[1]


	channel.basic_publish(exchange='xch_scope_b',
	                      body=pickle.dumps(data),
	                      routing_key=str(args.uuid))
	channel.basic_ack(delivery_tag=method.delivery_tag)



# Load all of the keys into memory so it should be reasonably fast when packets
# go flying
def init (args):
	global queries, additional

	mdb = connect_mongodb()

	lines = mdb[str(args.uuid)].find()

	for line in lines:
		queries[line['query'][0]] = line['query'][1]

		sub = additional.setdefault(line['query'][0], {})
		sub[line['query'][1]] = []

		for add in line['additional']:
			sub[line['query'][1]].append(add)

	l.info('Added queries: {}'.format(queries))
	l.info('Added additional: {}'.format(additional))


# Start the connection to rabbitmq

description = 'Meta - Key:Value'
settings = []
parameters = [('edit_url', str)]

gatdBlock.start_block(l, description, settings, parameters, process, init=init)
