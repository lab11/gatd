#!/usr/bin/env python

import json
import socket
import struct
import subprocess
import time
import Weather

import os

HOSTNAME = 'inductor.eecs.umich.edu'
PORT     = 4001
HOUR     = 3600

print os.getcwd()

while True:

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind(('', 10002))

		pid = 'nghjDMLmHY'

		while True:

			Weather.fetch()
			station = Weather.Station('KARB')

			m = dict(station.items())

			s.sendto(pid + json.dumps(m), (HOSTNAME, PORT))

			time.sleep(HOUR)

	except Exception, e:
		print "Suppressed excpetion", e
		time.sleep(5)

