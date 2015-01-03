
import pika
import pymongo

import gatdBlock
import gatdConfig
import gatdLog

l = gatdLog.getLogger('mongodb')

def connect_mongodb ():
	# get a mongo connection
	mc = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                         port=gatdConfig.mongo.PORT)
	mdb = mc['gatdv6']
	mdb.authenticate(gatdConfig.blocks.MDB_USERNAME,
	                 gatdConfig.blocks.MDB_PASSWORD)

	return mdb


def save (args, channel, method, prop, body):
	global mdb

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


try:
	mdb = connect_mongodb()

	# Start the connection to rabbitmq

	description = 'Save to MongoDB'
	settings = []
	parameters = []

	gatdBlock.start_block(l, description, settings, parameters, save)
except:
	l.exception('Mongo died')