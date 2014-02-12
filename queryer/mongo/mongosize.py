#!/usr/bin/env python2
import apscheduler.scheduler
import json
import os
import pika
import pymongo
import struct
import sys
import time

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

def getDBStats ():
	global amqp_conn, amqp_chan
	mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                                 port=gatdConfig.mongo.PORT)
	mongo_db   = mongo_conn[gatdConfig.mongo.DATABASE]
	mongo_db.authenticate(gatdConfig.mongo.USERNAME,
	                      gatdConfig.mongo.PASSWORD)

	stats = mongo_db.command('dbstats', gatdConfig.mongo.COL_FORMATTED)
	now = int(time.time()*1000)

	j = json.dumps({'profile_id': 'Wr6RQjmTMH',
	                'data':        json.dumps(stats),
	                'time':       now,
	                'port':       gatdConfig.mongo.PORT,
	                'ip_address': 0})

	pkt = ojson = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + j

	while True:
		try:
			amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
			                        body=pkt,
			                        routing_key='')
			break
		except pika.exceptions.ChannelClosed as e:
			amqp_conn = pika.BlockingConnection(
							pika.ConnectionParameters(
								host=gatdConfig.rabbitmq.HOST,
								port=gatdConfig.rabbitmq.PORT,
								credentials=pika.PlainCredentials(
									gatdConfig.rabbitmq.USERNAME,
									gatdConfig.rabbitmq.PASSWORD)
						))
			amqp_chan = amqp_conn.channel();

sched = apscheduler.scheduler.Scheduler(standalone=True)

amqp_conn = pika.BlockingConnection(
				pika.ConnectionParameters(
					host=gatdConfig.rabbitmq.HOST,
					port=gatdConfig.rabbitmq.PORT,
					credentials=pika.PlainCredentials(
						gatdConfig.rabbitmq.USERNAME,
						gatdConfig.rabbitmq.PASSWORD)
			))
amqp_chan = amqp_conn.channel();

sched.add_interval_job(func=getDBStats, hours=1)

sched.start()
