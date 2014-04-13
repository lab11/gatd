import ConfigParser
import copy
import glob
import json
import inspect
import IPy
import random
import string
import StringIO
import os
import sys
import uuid
import watchdog.observers
import watchdog.events

sys.path.append(os.path.abspath('../config'))
import gatdConfig

import FormatterExceptions as FE

class ParserWatcher (watchdog.events.FileSystemEventHandler):
	def __init__(self, pm):
		self.pm = pm

	def handle_change (self, filename):
		self.pm._loadParserFile(filename)

	def on_any_event (self, event):
		if not event.is_directory:
			if hasattr(event, 'src_path'):
				self.handle_change(event.src_path)
			if hasattr(event, 'dest_path'):
				self.handle_change(event.dest_path)


class profileManager (object):

	# Map of pid->config map
	# Stores all of the relevant information about each profile, like the parser
	# and whatnot.
	configs = {}

	# Map of ip addr->profile_id
	# Stores the correct profile ID to use given a particular input IP address.
	addrs   = {}

	# Default config example
	default_config  = {'parser': None,
	                   'no_parse': False
	                  }


	def __init__ (self, db):
		self.db = db

		# Setup the path to the external parsers
		externals_path = os.path.join(gatdConfig.gatd.EXTERNALS_ROOT,
		                              gatdConfig.formatter.EXTERNALS_PROFILES)
		sys.path.append(externals_path)

		# Load all parsers in and update any information in the database
		parsers = glob.glob(os.path.join(externals_path, '*.py'))
		for parser_file in parsers:
			self._loadParserFile(parser_file)

		self.observer = watchdog.observers.Observer()
		self.observer.schedule(ParserWatcher(self),
		                       externals_path,
		                       recursive=False)
		self.observer.start()

	def __str__ (self):
		out = 'addrs\n'
		for a in self.addrs:
			out += str(IPy.IP(a)) + ': ' + str(self.addrs[a]) + '\n'
		return out

	def _loadParserFile (self, filename):
		parser_name,parser_ext = os.path.splitext(os.path.basename(filename))

		# Check for files we don't want to parse
		if parser_ext != '.py':
			return
		if parser_name == 'parser':
			# Skip the base class
			return

		try:
			parser = self._getParser(parser_name)

			if not parser:
				print('Could not load parser {}'.format(parser_name))
				# Error occurred while loading the parser
				return

			# Find the special attributes that determine formatter behavior
			source_addrs = []
			no_parse = False
			if hasattr(parser, 'source_addrs'):
				source_addrs = parser.source_addrs
			if hasattr(parser, 'no_parse'):
				no_parse = parser.no_parse

			# All attributes that are strings are saved to be used in later
			# parts of the system
			meta = {}
			for m in inspect.getmembers(parser):
				if isinstance(m[1], basestring) and m[0][0] != '_':
					# Get all attributes that are strings and not system
					# attributes
					meta[m[0]] = m[1]

			# Check if we already know about this parser
			dbinfo = self.db.getProfileByParser(parser_name)

			# Get a profile id if this is new
			if dbinfo:
				profile_id = dbinfo['profile_id']
				# Save any information that may have changed
				self.db.updateProfile(dbinfo, meta)
			else:
				# Create a profile id and save it
				profile_id = self._createProfileId()
				self.db.addProfile(parser_name, profile_id, meta)

			# Save important information in memory for handling packets
			config = copy.copy(self.default_config)
			config['parser'] = parser
			config['no_parse'] = no_parse
			self.configs[profile_id] = config

			for source_addr in source_addrs:
				self._addAddr(source_addr, profile_id)

			print('Added profile {} with parser {}'.format(profile_id,
				parser_name))

		except TypeError as typee:
			# Skip error with trying to import __init__.py
			pass

	def _addAddr (self, ip_str, pid):
		# Add the IP address to the dict
		ip = IPy.IP(ip_str, ipversion=6)
		self.addrs[ip.int()] = pid

	def _createProfileId (self):
		pid = ''.join(random.choice(string.letters + string.digits) \
			for x in range(10))
		return pid

	def _getParser (self, parser_name):
		# Load or reload the python parser

		try:
			if parser_name not in sys.modules:
				# Import the first time
				__import__(parser_name)
				parser_mod = sys.modules[parser_name]
			else:
				# Reload the second time
				parser_mod = sys.modules[parser_name]
				reload(parser_mod)
			parser_n   = getattr(parser_mod, parser_name)
			# Create a parser object to use for parsing matching
			# incoming packets
			parser     = parser_n()
			return parser
		except ImportError:
			# Tried to import but the file wasn't there
			# We should delete the profile from the db because the parser
			# file is gone, but that could be dangerous, so we won't do that
			# for now.
			return None
		except AttributeError:
			# Tried to access the parser class that is the same name of the
			# file but that failed. That means the author messed up.
			return None
		except Exception:
			# This could fail if the user doesn't name things correctly
			# But we don't want to crash the entire formatter so catch
			# everything and return None
			return None

	def getPacketPid (self, addr, data):
		if addr != None:
			ip = IPy.IP(addr)
			if ip.int() in self.addrs:
				return self.addrs[ip.int()]

		if len(data) > 10:
			pid = data[0:10]
			if pid in self.configs:
				return pid

		return None

	# Check if an IP address of an incoming packet is recognized or not
	def isPacketKnown (self, data, meta):
		addr = meta['addr'] if ('addr' in meta) else None
		return self.getPacketPid(addr=addr, data=data) != None

	# Do the parse of the actual data packet
	# Returns a dict
	# Raises exception if parser is bad
	def parsePacket (self, data, meta):
		addr = meta['addr'] if ('addr' in meta) else None
		pid  = self.getPacketPid(addr=addr, data=data)

		if pid == None:
			# Don't recognize this packet
			raise FE.ParserNotFound("No parser for this packet.")

		config = self.configs[pid]
		parser = config['parser']

		# Create dict of settings that need to get passed to parser
		psettings = {}

		# need to fill in extra at some point
		extra = {}

		try:
			# Check if the data source comes as JSON, and we don't need to
			# format it
			if config['no_parse']:
				# Just parse the data as JSON
				jsonpkt = json.loads(data[10:])
				if meta['_receiver'] == 'http_post':
					if jsonpkt['headers']['content-type'] == 'application/json':
						r = json.loads(jsonpkt['data'])
				else:
					r = jsonpkt

				r['address'] = str(meta['addr'])
				r['time']    = meta['time']
				r['port']    = meta['port']

			else:
				# Use a parser
				r = parser.parse(data=data,
				                 meta=meta,
				                 extra=extra,
				                 settings=psettings)
				if r == None:
					# Just dump this packet
					return None
		except Exception as e:
			print('Bad Parser: {}'.format(e))
			r = None

		if type(r) != dict:
			raise FE.ParserError('Parser does not return a dict.')

		# Require that the profile ID is set
		r['profile_id'] = pid

		# Set this as a raw packet by setting processor count to 0
		r['_processor_count'] = 0

		# Note how we got this packet
		if '_receiver' in meta:
			r['_receiver'] = meta['_receiver']

		# Add in the meta data
		r.update(self.db.getMeta(r))

		# Add in the gateway data
		r.update(self.db.getGatewayKeys(addr >> 64))

		return r

if __name__ == '__main__':
	import time
	import MongoInterface
	mi = MongoInterface.MongoInterface()
	p = profileManager(mi)

	time.sleep(1000000)
