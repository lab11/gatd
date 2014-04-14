#!/usr/bin/env python2

import apscheduler.scheduler
import ConfigParser as configparser
import json
import os
import pika
import pymongo
import struct
import sys
import time

import setproctitle
setproctitle.setproctitle('gatd-q: mongosize')

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

profile_id = ''

def getDBStats ():
	global profile_id
	mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                                 port=gatdConfig.mongo.PORT)
	mongo_db   = mongo_conn[gatdConfig.mongo.DATABASE]
	mongo_db.authenticate(gatdConfig.mongo.USERNAME,
	                      gatdConfig.mongo.PASSWORD)

	stats = mongo_db.command('dbstats', gatdConfig.mongo.COL_FORMATTED)
	now = int(time.time()*1000)

	j = json.dumps({'profile_id': profile_id,
	                'data':       json.dumps(stats),
	                'time':       now,
	                'port':       gatdConfig.mongo.PORT,
	                'ip_address': 0})

	print(j)

	pkt = ojson = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + j

	amqp_conn = pika.BlockingConnection(
					pika.ConnectionParameters(
						host=gatdConfig.rabbitmq.HOST,
						port=gatdConfig.rabbitmq.PORT,
						credentials=pika.PlainCredentials(
							gatdConfig.rabbitmq.USERNAME,
							gatdConfig.rabbitmq.PASSWORD)
				))
	amqp_chan = amqp_conn.channel()

	amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
	                        body=pkt,
	                        routing_key='')


sched = apscheduler.scheduler.Scheduler(standalone=True)

externals_path = os.path.join(gatdConfig.gatd.EXTERNALS_ROOT,
                              gatdConfig.queryer.EXTERNALS_MONGO_SIZE)
cfgp = configparser.ConfigParser()
cfgp.read(os.path.join(externals_path, 'gatd.config'))
profile_id = cfgp.get('main', 'profile_id')

sched.add_interval_job(func=getDBStats, minutes=30)

sched.start()
