#!/usr/bin/env python2

import apscheduler.scheduler
import ConfigParser as configparser
import glob
import IPy
import json
import os
import pika
import re
import socket
import struct
import sys
import time

import setproctitle
setproctitle.setproctitle('gatd-q: wemo')

# Enable logging in case apscheduler catches an error
import logging
logging.basicConfig()

sys.path.append(os.path.abspath('../../config'))
import gatdConfig

test = """GET /setup.xml
HOST: {ipaddr}:{port}
User-Agent: GATD-HTTP/1.0"""
hdr = """POST /upnp/control/{commandcat}1 HTTP/1.1
SOAPACTION: "urn:Belkin:service:{commandcat}:1#{command}"
Content-Length: {length}
Content-Type: text/xml; charset="utf-8"
HOST: {ipaddr}:{port}
User-Agent: GATD-HTTP/1.0"""
body = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" \
s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
 <s:Body>
  <u:{command} xmlns:u="urn:Belkin:service:{commandcat}:1">
    {argument}
  </u:{command}>
 </s:Body>
</s:Envelope>
"""
argument = """<{argumentname}>{value}</{argumentname}>"""

PROFILE_ID = 'fyMfyFW1aU'



# Connect to the wemo and return a socket and the port used to connect
def findPort (hostname):
	for i in range(0,3):
		connection_attempts = 2
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		while connection_attempts > 0:
			try:
				sock.connect((hostname, 49152 + i))
				sock.settimeout(0.1)
				testreq = test.format(ipaddr=hostname,port=49152+i)
				testreq = testreq.replace('\n', '\r\n') + '\r\n\r\n'
				sock.send(testreq)
				sock.recv(16)
				return 49152 + i
			except socket.error:
				connection_attempts -= 1
	return None

def connect (hostname):
	port = findPort(hostname)
	if port == None:
		return None
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((hostname, port))
	sock.settimeout(0.3)
	return (sock, port)

def soapMessage (hostname, cat, cmd, resp=False, argname=None, arg=None):
	conn = connect(hostname)
	if conn == None:
		# Couldn't connect to wemo
		return
	sock = conn[0]
	port = conn[1]

	if arg != None:
		arguments = argument.format(argumentname=argname, value=arg)
	else:
		arguments = ''
	soap_bdy = body.format(command=cmd, commandcat=cat, argument=arguments)
	soap_hdr = hdr.format(command=cmd,
	                      commandcat=cat,
	                      length=len(soap_bdy),
	                      ipaddr=hostname,
	                      port=port)
	soap_hdr = soap_hdr.replace('\n', '\r\n')
	soap = soap_hdr + '\r\n\r\n' + soap_bdy
	sock.send(soap)

	message = ''
	if resp:
		response = ''
		while True:
			data = sock.recv(1024)
			response += data
			if '</s:Envelope>' in response:
				break
		message = response.split('\r\n\r\n', 1)[1]
		if argname:
			reg = re.compile('<{argumentname}>(.*)</{argumentname}>'.format(
				argumentname=argname))
			message = reg.search(response).group(1)
	sock.close()
	return (port, message)


def queryWemo (hostname, mac_addr, wemo_type):
	global ampq_conn, amqp_chan
	if wemo_type == 'insight':
		status_response = soapMessage(hostname, 'basicevent', 'GetBinaryState',
		                              True, argname='BinaryState')
		port   = status_response[0]
		status = bool(int(status_response[1]))
		power  = float(soapMessage(hostname, 'insight', 'GetPower', True,
		                           argname='InstantPower')[1])/1000.0

		ip_address = socket.gethostbyname(hostname)
		try:
			addr = IPy.IP(IPy.IPint(ip_address)).v46map().int()
		except ValueError:
			# This was apparently already an IPv6 address
			addr = IPy.IPint(ip_address).int()

		j = json.dumps({'profile_id': PROFILE_ID,
		                'data':       json.dumps({'load_on': status,
		                                          'watts': power,
		                                          'mac_addr': mac_addr,}),
		                'time':       int(time.time()*1000),
		                'port':       port,
		                'ip_address': addr})

		pkt = struct.pack('B', gatdConfig.pkt.TYPE_QUERIED) + j

		print(pkt)

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
	hostname  = cfgp.get('main', 'hostname')
	wemo_type = cfgp.get('main', 'type')
	frequency = int(cfgp.get('main', 'frequency'))
	mac_addr  = cfgp.get('main', 'macaddr')

	print('Adding job for {} from {}'.format(hostname, config))

	sched.add_interval_job(func=queryWemo,
	                       seconds=frequency,
	                       kwargs={'hostname':hostname, 'wemo_type':wemo_type,
	                               'mac_addr':mac_addr})

sched.start()



