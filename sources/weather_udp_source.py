#!/usr/bin/env python

import json
import socket
import struct
import subprocess
import time
import Weather

import setproctitle
setproctitle.setproctitle('gatd-src: weather')

import os

HOSTNAME = 'gatd.com'
PORT     = 4001
HOUR     = 3600
PID      = 'ABCDEFGHIJ'

print os.getcwd()

while True:

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind(('', 10002))

		while True:

			Weather.fetch()
			station = Weather.Station('KARB')

			m = dict(station.items())

			s.sendto(PID + json.dumps(m), (HOSTNAME, PORT))

			time.sleep(HOUR)

	except Exception, e:
		print "Suppressed excpetion", e
		time.sleep(5)

