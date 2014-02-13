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

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig


request_header = {'User-Agent': 'GATD-queryer'}

def httpGET (url, profile_id, unique_id):
	global amqp_conn, amqp_chan
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

		d = {'profile_id': profile_id,
		     'data':       r.text,
		     'time':       now,
		     'port':       urlparsed.port or 80,
		     'ip_address': addr}
		if unique_id:
			d['unique_id'] = unique_id

		pkt = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + json.dumps(d)

		while True:
			try:
				amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
				                        body=pkt,
				                        routing_key='')
				break
			except pika.exceptions.ChannelClosed:
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
	try:
		unique_id = cfgp.get('main', 'unique_id')
	except Exception:
		unique_id = None


	sched.add_interval_job(func=httpGET,
	                       seconds=frequency,
	                       kwargs={'url':url, 'profile_id':profile_id,
	                               'unique_id':unique_id})

sched.start()
