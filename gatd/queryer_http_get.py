#!/usr/bin/env python3

import sys

import arrow
import apscheduler.scheduler
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
		pkt['time_utc_iso'] = now
		pkt['data'] = {'body': r.text,
		               'headers': r.headers,
		               'url': url}

		# Connect to rabbitmq
		amqp_conn = pika.BlockingConnection(
								pika.ConnectionParameters(
									host=gatdConfig.rabbitmq.HOST,
									port=gatdConfig.rabbitmq.PORT,
									credentials=pika.PlainCredentials(
										gatdConfig.queryer_http_get.USERNAME,
										gatdConfig.queryer_http_get.PASSWORD)
							))
		amqp_chan = amqp_conn.channel();

		amqp_chan.basic_publish(exchange='xch_queryer_http_get',
		                        body=pkt,
		                        routing_key=block_uuid)
		amqp_chan.close()


if len(sys.argv) < 4:
	l.error('Not enough arguments.')
	print('usage: {} <block uuid> <URL> <interval (seconds)>'.format(sys.argv[0]))
	sys.exit(1)

block_uuid = sys.argv[1]
try:
	u = uuid.UUID(block_uuid)
except:
	l.errro('Block UUID is an invalid UUID ({})'.format(sys.argv[1]))
	print('Invalid block UUID')
	sys.exit(1)
url = sys.argv[2]
try:
	interval = int(sys.argv[3])
except:
	l.error('Interval must be an integer.')
	print('Interval ({}) must be an integer.'.format(sys.argv[3]))
	sys.exit(1)

l.info('Started with UUID:{}, URL:{}, interval:{}'.format(block_uuid, url, interval))


sched = apscheduler.scheduler.Scheduler(standalone=True)

sched.add_interval_job(func=httpGET,
                       seconds=interval,
                       kwargs={'url':url, 'block_uuid':block_uuid})

sched.start()
