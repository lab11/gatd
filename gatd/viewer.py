

import pika
import pymongo

import gatdBlock
import gatdConfig
import gatdLog

l = gatdLog.getLogger('streamer-socketio')

mdb = None


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
		query = {'uuid': str(args.uuid)}
		push  = {'$push': {
					'packets': {
						'$each': [body],
						'$slice': -10
					}
				}}

		l.debug('Adding packet to viewer (uuid:{})'.format(args.uuid))

		existing = mdb['viewer'].find_one(query)
		if not existing:
			l.debug('First packet for this stream.')
			mdb['viewer'].insert(query)

		mdb['viewer'].update(query, push, upsert=True)

		channel.basic_ack(delivery_tag=method.delivery_tag)

	except pymongo.errors.AutoReconnect as e:
		l.exception('Going to try to reconnect to mongodb.')

	except pymongo.errors.ConnectionFailure as e:
		l.exception('Lost connection to mongodb.')
		mdb = connect_mongodb()

	except:
		l.exception('Other exception in viewer')


try:
	mdb = connect_mongodb()

	# Start the connection to rabbitmq

	description = 'Save recent packets for the viewer'
	settings = []
	parameters = [('url', str)]

	gatdBlock.start_block(l, description, settings, parameters, save)
except:
	l.exception('Issue connecting to MongoDB')
