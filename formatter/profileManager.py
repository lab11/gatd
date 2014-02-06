import ConfigParser
import copy
import glob
import IPy
import random
import string
import StringIO
import os
import sys
import uuid

import FormatterExceptions as FE

class profileManager:

	# Map of pid->config map
	# Stores all of the relevant information about each profile, like the parser
	# and whatnot.
	configs = {}

	# Map of ip addr->profile_id
	# Stores the correct profile ID to use given a particular input IP address.
	addrs   = {}

	# Default config example
	default_config  = {'name': None,
	                   'parser': None,
	                   'access': 'public'
	                  }


	def __init__ (self, db):
		self.db = db

		# Load all parsers in and update any information in the database
		parsers = glob.glob('parsers/*.py')
		for parser_file in parsers:
			print('working on {}'.format(parser_file))
			try:
				parser_name = os.path.splitext(os.path.basename(parser_file))[0]
				parser = self._getParser(parser_name)

				profile_name = ''
				access = 'public'
				source_addrs = []

				if hasattr(parser, 'name'):
					profile_name = parser.name
				if hasattr(parser, 'access'):
					access = parser.access
				if hasattr(parser, 'source_addrs'):
					source_addrs = parser.source_addrs

				# Check if we already know about this parser
				dbinfo = db.getConfigByParser(parser_name)

				if dbinfo:
					profile_id = dbinfo['profile_id']
					print('got db info {}'.format(profile_id))
				else:
					# Create a profile id and save it
					profile_id = self._createProfileId()
					db.storeConfig(parser_name, profile_id)
					print('added to db')

				# Store all of the info in the dicts in this instance
				config = copy.copy(self.default_config)
				config['name'] = profile_name
				config['parser'] = parser
				config['access'] = access
				self.configs[profile_id] = config

				for source_addr in source_addrs:
					self.addrs[source_addr] = profile_id

			except Exception as e:
				pass

	def __str__ (self):
		out = 'addrs\n'
		for a in self.addrs:
			out += str(IPy.IP(a)) + ': ' + str(self.addrs[a]) + '\n'
		return out

	def _addAddr (self, ip_str, pid):
		# Add the IP address to the dict
		ip = IPy.IP(ip_str, ipversion=6)
		self.addrs[ip.int()] = pid

	def _createProfileId (self):
		pid = ''.join(random.choice(string.letters + string.digits) for x in range(10))
		return pid

	def _getParser (self, parser_name):
		# Load the python parser

		exec('import parsers.{}'.format(parser_name))
		parser_mod = sys.modules['parsers.{}'.format(parser_name)]
		parser_n   = getattr(parser_mod, parser_name)
		# Create a parser object to use for parsing matching incoming packets
		parser     = parser_n()
		return parser

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

		# Set the public key->value
		try:
			if config['access'] == 'public':
				psettings['public'] = True
		except KeyError:
			psettings['public'] = False


		# need to fill in extra at some point
		extra = {}

		try:
			r = parser.parse(data=data, meta=meta, extra=extra, settings=psettings)
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

		# Add in the meta data
		r.update(self.db.getMeta(r))

		# Add in the gateway data
		r.update(self.db.getGatewayKeys(addr >> 64))

		return r
