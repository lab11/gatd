

import pika
import pymongo
import setproctitle

setproctitle.setproctitle('gatd:db:mon')

import gatdBlock
import gatdLog

l = gatdLog.getLogger('mongodb')

args = None
routing_keys = None

def connect_mongodb ():
	# get a mongo connection
	mc = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                         port=gatdConfig.mongo.PORT)
	mdb = mc['gatdv6']
	mdb.authenticate(gatdConfig.blocks.MDB_USERNAME,
	                 gatdConfig.blocks.MDB_PASSWORD)

	return mdb


def save (channel, method, prop, body):

	try:
		# No magic here, just try to insert the record into the capped collection
		mdb[str(args.uuid)].insert(body)

		channel.basic_ack(delivery_tag=method.delivery_tag)

	except pymongo.errors.AutoReconnect as e:
		l.exception('Going to try to reconnect to mongodb.')

	except pymongo.errors.ConnectionFailure as e:
		l.exception('Lost connection to mongodb.')
		mdb = connect_mongodb()

	except:
		l.exception('Other exception in saving to mongo')



mdb = connect_mongodb()

# Start the connection to rabbitmq

description = 'Save to MongoDB'
settings = []
parameters = []

gatdBlock.start_block(l, description, settings, parameters, save)
