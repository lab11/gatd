

import pika
import pymongo
import setproctitle

setproctitle.setproctitle('gatd:str:sio')

import gatdBlock
import gatdLog

l = gatdLog.getLogger('streamer-socketio')

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


def save_packet (channel, method, prop, body):

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
		l.exception('Other exception in streamer')



mdb = connect_mongodb()

# Make sure that the capped collection exists
mdb.create_collection(name=str(args.uuid),
                      capped=True,
                      size=1073741824) # 1.0 GB in bytes


# Start the connection to rabbitmq

description = 'Socket.io Streaming'
settings = []
parameters = ['url']

gatdBlock.start_block(l, description, settings, parameters, save)
