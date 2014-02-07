#!/usr/bin/env python3
import apscheduler.scheduler
import ConfigParser as configparser
import glob
import IPy
import json
import os
import requests
import socket
import struct
import sys
import time
import urlparse

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig


request_header = {'User-Agent': 'GATD-queryer'}

def getXML (url, profile_id):
	r = requests.get(url, headers=request_header)
	now = int(time.time()*1000)

	if r.status_code == 200:
		urlparsed = urlparse.urlparse(url)

		ip_address = socket.gethostbyname(urlparsed.hostname)
		try:
			addr = IPy.IP(IPy.IPint(ip_address)).v46map().int()
		except ValueError:
			# This was apparently already an IPv6 address
			addr = IPy.IPint(ip_address).int()

		j = json.dumps({'profile_id': profile_id,
		                'xml':        r.text,
		                'time':       now,
		                'port':       urlparsed.port or 80,
		                'ip_address': addr})

		pkt = ojson = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + j

		amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
		                        body=pkt,
		                        routing_key='')


sched = apscheduler.scheduler.Scheduler(standalone=True)
cfgp = configparser.ConfigParser()

amqp_conn = pika.BlockingConnection(
				pika.ConnectionParameters(
					host=gatdConfig.rabbitmq.HOST,
					port=gatdConfig.rabbitmq.PORT,
					credentials=pika.PlainCredentials(
						gatdConfig.rabbitmq.USERNAME,
						gatdConfig.rabbitmq.PASSWORD)
			))
amqp_chan = amqp_conn.channel();

# Load all config files
configs = glob.glob('configs/*.config')
for config in configs:
	cfgp.read(config)
	profile_id = cfgp.get('main', 'profile_id')
	url        = cfgp.get('main', 'url')
	frequency  = int(cfgp.get('main', 'frequency'))

	sched.add_interval_job(func=getXML,
	                       seconds=frequency,
	                       kwargs={'url':url, 'profile_id':profile_id})

sched.start()
