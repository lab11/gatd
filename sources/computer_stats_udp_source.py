#!/usr/bin/env python3

import sys,os
import json
import psutil
import socket
import errno
import struct
import subprocess
import time
from numpy import array
from math import log,ceil

import setproctitle
setproctitle.setproctitle('gatd-src: computer usage')

from threading import Thread
# Py{2,3}k
try:
	import Queue as queue
except ImportError:
	import queue
measurements = queue.Queue()

################################################################################
## CONFIGURATION

try:
	import configparser
except ImportError:
	print("Are you running python 3?")
	raise

DEFAULTS = {
		'hostname'   : 'localhost',
		'port'       : '4001',
		'profile_id' : 'ABCDEFGHIJ',

		# Seconds to sleep between collection data points, may be float, minimum 0.1
		'data_resolution' : '3',

		# How often to send batches of packets, unit is seconds
		'packet_interval_ac' : '3',
		'packet_interval_battery' : '60',
		}

config_all = configparser.ConfigParser(DEFAULTS)
config_all.read('computer_stats_udp_source.conf')
config = config_all['DEFAULT']

## END CONFIGURATION
################################################################################

if float(config['data_resolution']) > float(config['packet_interval_ac']) or\
		float(config['data_resolution']) > float(config['packet_interval_battery']):
	print("Configuration Error: DATA_RESOLUTION must be <= PACKET_INTERVAL")
	print("(You can't send packets more frequently that you're sampling data...)")
	raise ValueError


## Adaptive Reporting
##
## Can't do callbacks without a glib main loop, so... poll every packet sending
power_func=None
PACKET_INTERVAL=float(config['packet_interval_ac'])

def onPowerChange(args, kwargs):
	global PACKET_INTERVAL
	if dev.GetProperty('ac_adapter.present'):
		if PACKET_INTERVAL != float(config['packet_interval_ac']):
			PACKET_INTERVAL = float(config['packet_interval_ac'])
			print('On AC power, packet interval set to {}'.format(PACKET_INTERVAL))
	else:
		if PACKET_INTERVAL != float(config['packet_interval_battery']):
			PACKET_INTERVAL = float(config['packet_interval_battery'])
			print('On battery power, packet interval set to {}'.format(PACKET_INTERVAL))

try:
	import dbus

	bus = dbus.SystemBus()
	hal_obj = bus.get_object ('org.freedesktop.Hal', '/org/freedesktop/Hal/Manager')
	hal = dbus.Interface (hal_obj, 'org.freedesktop.Hal.Manager')

	try:
		dev_obj = bus.get_object ("org.freedesktop.Hal", hal.FindDeviceByCapability ("ac_adapter")[0])
		global dev
		dev = dbus.Interface (dev_obj, "org.freedesktop.Hal.Device")
		#dev.connect_to_signal ("PropertyModified", onPowerChange)
		power_func=onPowerChange
		PACKET_INTERVAL=0
		onPowerChange(None, None)

	except IndexError:
		print('No AC adaptor found on dbus; no power management hooks')
		print('will be enabled for this session')
except ImportError:
	print('Failed to import dbus module! power managment hooks disabled')
	print('(try installing python-dbus?)')
except dbus.exceptions.DBusException:
	print('Dbus exception; no power managment hooks')
	print('will be enabled for this session')


#################
# psutil wrappers
def get_name ():
	return socket.getfqdn()

def get_cpu_percent ():
	return psutil.cpu_percent()

def get_memory_percent ():
	return psutil.phymem_usage()[3]

def get_disk_percent ():
	return psutil.disk_usage('/')[3]


#####################
# Spawn sender thread

def sender():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('', 10001))

	batched = []
	backlog = []

	while True:
		try:
			batched.append(measurements.get())
			print("[%3d]: %s" % (len(batched), m))

			if len(batched) >= (PACKET_INTERVAL / float(config['data_resolution'])):
				backlog.extend(batched)
				try:
					for p in backlog:
						s.sendto(p, (config['hostname'], int(config['port'])))
					print("\033[1;32mSent %d packet%s at %s\033[m\n" %\
						(len(backlog),
						('s','')[len(backlog)==1],
						time.ctime()),
						)
					backlog = []
				except socket.gaierror as e:
					if e.errno != -errno.EIO:
						raise e
					print("\033[1;33mBacklogged %d packet%s at %s\033[m" %\
						(len(batched),
						('s','')[len(batched)==1],
						time.ctime()),
						)
					print("\t\033[0;33mCurrent backlog: %d\033[m\n" %\
						(len(backlog)),
						)
				batched = []
				if power_func:
					power_func(None, None)
		except Exception as e:
			print("Suppressed excpetion: {}".format(e))
			time.sleep(1)

sender_thread = Thread(target=sender)
sender_thread.daemon = True
sender_thread.start()


#######################
# Main data logger loop

while True:
	try:
		# Sliding window size, probably want relatively small
		amax = 32
		aidx = -1

		ls, lr = (-1, -1)

		while True:
			time.sleep(float(config['data_resolution']))

			# Network
			js,jr = psutil.network_io_counters()[0:2]
			sent = js - ls
			recv = jr - lr
			ls,lr = (js, jr)
			if (sent > js) or (sent < 0) or (recv < 0):
				# only possible if ls is neg, aka first round
				# also possible for byte counter rollover
				continue

			if (aidx == -1):
				sent_array = array([sent] * amax)
				recv_array = array([recv] * amax)
				aidx = 0
			else:
				sent_array[aidx] = sent
				recv_array[aidx] = recv
				aidx = (aidx + 1) % amax

			scale = 10
			try:
				sc = scale**ceil(log(sent_array.max(),scale)+1)
			except ValueError:
				sc = 1
			try:
				rc = scale**ceil(log(recv_array.max(),scale)+1)
			except ValueError:
				rc = 1

			sc = max(10,sc)
			rc = max(10,rc)
			# End Network

			m = {
			 'time': time.time() * 1000,
			 'name': get_name(),
			 'cpu': get_cpu_percent(),
			 'memory': get_memory_percent(),
			 'net-sent' : (sent / sc) * 100,
			 'net-recv' : (recv / rc) * 100,
			 'disk': get_disk_percent()
			}

			pkt = config['profile_id'] + json.dumps(m)
			measurements.put(pkt.encode('utf-8'))
	
	except Exception as e:
		print("Suppressed excpetion: {}".format(e))
		time.sleep(1)

