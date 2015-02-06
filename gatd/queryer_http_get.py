#!/usr/bin/env python3

"""
Issue HTTP GET requests to get data packets.
"""

import argparse
import asyncio
import pickle
import sys
import uuid

import arrow
import apscheduler.schedulers.asyncio
import pika
import requests

import gatdConfig
import gatdLog

l = gatdLog.getLogger('query-HTTP-get')

request_header = {'User-Agent': 'GATD-queryer'}

def httpGET (url, block_uuid):
	try:
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
			pkt['headers'] = dict(r.headers)
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

			amqp_chan.basic_publish(exchange='xch_scope_a',
			                        body=pkt_pickle,
			                        routing_key=block_uuid)
			amqp_chan.close()

	except:
		l.exception('Error in HTTP GET')


parser = argparse.ArgumentParser(description='HTTP Get Query')

parser.add_argument('--url',
                    type=str,
                    required=True)

parser.add_argument('--interval',
                    type=int,
                    required=True)

parser.add_argument('--uuid',
                    type=uuid.UUID,
                    required=True)
parser.add_argument('--source_uuid',
                    nargs='*',
                    type=uuid.UUID)

args = parser.parse_args()

l.info('URL: {}'.format(args.url))

try:
	sched = apscheduler.schedulers.asyncio.AsyncIOScheduler(standalone=True)
	sched.add_executor('processpool')
	sched.add_job(func=httpGET,
	              trigger='interval',
	              seconds=args.interval,
	              kwargs={'url':args.url, 'block_uuid':str(args.uuid)})
	sched.start()
except:
	l.exception('No good')

try:
	asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
	l.info('ctrl+c, exiting')
except:
	l.exception('Error')
