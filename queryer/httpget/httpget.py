#!/usr/bin/env python2
import apscheduler.scheduler
import ConfigParser as configparser
import glob
import IPy
import json
import os
import pika
import requests
import socket
import struct
import sys
import time
import urlparse

import setproctitle
setproctitle.setproctitle('gatd-q: httpget')

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig


request_header = {'User-Agent': 'GATD-queryer'}

def httpGET (url, profile_id, unique_id):
	try:
		r = requests.get(url, headers=request_header, timeout=1)
	except Exception:
		# Something went wrong
		print('Could not get HTTP page: {}'.format(url))
		return

	now = int(time.time()*1000)

	print('got HTTP page: {}'.format(url))

	if r.status_code == 200:
		urlparsed = urlparse.urlparse(url)

		ip_address = socket.gethostbyname(urlparsed.hostname)
		try:
			addr = IPy.IP(IPy.IPint(ip_address)).v46map().int()
		except ValueError:
			# This was apparently already an IPv6 address
			addr = IPy.IPint(ip_address).int()

		d = {'profile_id': profile_id,
		     'data':       r.text,
		     'time':       now,
		     'port':       urlparsed.port or 80,
		     'ip_address': addr}
		if unique_id:
			d['unique_id'] = unique_id

		pkt = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + json.dumps(d)


		# Connect to rabbitmq
		amqp_conn = pika.BlockingConnection(
								pika.ConnectionParameters(
									host=gatdConfig.rabbitmq.HOST,
									port=gatdConfig.rabbitmq.PORT,
									credentials=pika.PlainCredentials(
										gatdConfig.rabbitmq.USERNAME,
										gatdConfig.rabbitmq.PASSWORD)
							))
		amqp_chan = amqp_conn.channel();

		amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
		                        body=pkt,
		                        routing_key='')
		amqp_chan.close()



sched = apscheduler.scheduler.Scheduler(standalone=True)
cfgp = configparser.ConfigParser()

# Load all config files
externals_path = os.path.join(gatdConfig.gatd.EXTERNALS_ROOT,
                              gatdConfig.queryer.EXTERNALS_HTTP)
configs = glob.glob(os.path.join(externals_path, '*.config'))
for config in configs:
	cfgp.read(config)
	profile_id = cfgp.get('main', 'profile_id')
	url        = cfgp.get('main', 'url')
	frequency  = int(cfgp.get('main', 'frequency'))
	try:
		unique_id = cfgp.get('main', 'unique_id')
	except Exception:
		unique_id = None


	sched.add_interval_job(func=httpGET,
	                       seconds=frequency,
	                       kwargs={'url':url, 'profile_id':profile_id,
	                               'unique_id':unique_id})

sched.start()
