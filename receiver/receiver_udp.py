#!/usr/bin/env python2

import IPy
import json
import pika
import struct
import time
import os
import socket
import sys

import setproctitle
setproctitle.setproctitle('gatd-r: py-udp')

sys.path.append(os.path.abspath('../config'))
import gatdConfig

addr_info = socket.getaddrinfo('::0', gatdConfig.receiver.PORT_UDP)

s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
s.bind(addr_info[0][-1])

amqp_conn = pika.BlockingConnection(
			pika.ConnectionParameters(
				host=gatdConfig.rabbitmq.HOST,
				port=gatdConfig.rabbitmq.PORT,
				credentials=pika.PlainCredentials(
					gatdConfig.rabbitmq.USERNAME,
					gatdConfig.rabbitmq.PASSWORD)
		))
amqp_chan = amqp_conn.channel();

while True:
	d, pkt_addr = s.recvfrom(1000)
	now = int(time.time()*1000)

	src_addr = pkt_addr[0]
	src_port = pkt_addr[1]

	# Get the IPv6 address in integer form
	try:
		addr = IPy.IP(IPy.IPint(src_addr)).v46map().int()
	except ValueError:
		# This was apparently already an IPv6 address
		addr = IPy.IPint(src_addr).int()


	amqp_pkt = struct.pack("!BQQHQ",
			gatdConfig.pkt.TYPE_UDP,
			addr>>(64*8),
			addr,
			src_port,
			now)

	amqp_pkt += d

	amqp_chan.basic_publish(exchange=gatdConfig.rabbitmq.XCH_RECEIVE,
	                        body=amqp_pkt,
	                        routing_key='')
	print(amqp_pkt)
