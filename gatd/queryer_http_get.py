#!/usr/bin/env python3

import asyncio
import pickle
import sys
import uuid

import arrow
import apscheduler.schedulers.asyncio
import pika
import requests
import setproctitle
setproctitle.setproctitle('gatd-q: httpget')

# Enable logging in case apscheduler catches an error
# import logging
# logging.basicConfig()

import gatdConfig
import gatdLog

l = gatdLog.getLogger('query-HTTP-get')

request_header = {'User-Agent': 'GATD-queryer'}

def httpGET (url, block_uuid):
	try:
		r = requests.get(url, headers=request_header, timeout=1)
	except Exception:
		# Something went wrong
		l.warn('Could not get HTTP page: {}'.format(url))
		return

	now = arrow.utcnow().isoformat()

	l.info('got HTTP page: {}'.format(url))

	if r.status_code == 200:
		pkt = {}
		pkt['src'] = 'query_http_get'
		pkt['time_utc_iso'] = now
		pkt['headers'] = r.headers
		pkt['http_get_url'] = url
		pkt['data'] = r.text

		pkt_pickle = pickle.dumps(pkt)

		l.debug('sending page. key:{} len:{}'.format(block_uuid, len(r.text)))

		# Connect to rabbitmq
		amqp_conn = pika.BlockingConnection(
								pika.ConnectionParameters(
									host=gatdConfig.rabbitmq.HOST,
									port=gatdConfig.rabbitmq.PORT,
									virtual_host=gatdConfig.rabbitmq.VHOST,
									credentials=pika.PlainCredentials(
										gatdConfig.blocks.RMQ_USERNAME,
										gatdConfig.blocks.RMQ_PASSWORD)
							))
		amqp_chan = amqp_conn.channel();

		amqp_chan.basic_publish(exchange='xch_queryer_http_get',
		                        body=pkt_pickle,
		                        routing_key=block_uuid)
		amqp_chan.close()


if len(sys.argv) < 4:
	l.error('Not enough arguments.')
	l.error('usage: {} <block uuid> <URL> <interval (seconds)>'.format(sys.argv[0]))
	sys.exit(1)

block_uuid = sys.argv[1]
try:
	u = uuid.UUID(block_uuid)
except:
	l.exception('Block UUID is an invalid UUID ({})'.format(sys.argv[1]))
	sys.exit(1)
url = sys.argv[2]
try:
	interval = int(sys.argv[3])
except:
	l.error('Interval ({}) must be an integer.'.format(sys.argv[3]))
	sys.exit(1)

l.info('Started with UUID:{}, URL:{}, interval:{}'.format(block_uuid, url, interval))


# Make sure the exchange exists
amqp_conn = pika.BlockingConnection(
				pika.ConnectionParameters(
					host=gatdConfig.rabbitmq.HOST,
					port=gatdConfig.rabbitmq.PORT,
					virtual_host=gatdConfig.rabbitmq.VHOST,
					credentials=pika.PlainCredentials(
						gatdConfig.blocks.RMQ_USERNAME,
						gatdConfig.blocks.RMQ_PASSWORD)
			))
amqp_chan = amqp_conn.channel();

amqp_chan.exchange_declare(exchange='xch_queryer_http_get',
                           exchange_type='direct',
                           durable='true')
amqp_chan.close()

sched = apscheduler.schedulers.asyncio.AsyncIOScheduler(standalone=True)
sched.add_executor('processpool')
sched.add_job(func=httpGET,
              trigger='interval',
              seconds=interval,
              kwargs={'url':url, 'block_uuid':block_uuid})

sched.start()

try:
	asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
	l.info('ctrl+c, exiting')
