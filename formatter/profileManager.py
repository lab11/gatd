import ConfigParser
import copy
import FormatterExceptions as FE
import IPy
import random
import string
import StringIO
import sys
import uuid

class profileManager:

	# Map of pid->config map
	# Stores all of the relevant information about each profile, like the parser
	# and whatnot.
	configs = {}

	# Map of ip addr->profile_id
	# Stores the correct profile ID to use given a particular input IP address.
	addrs   = {}

	# Map of parser name to pid
	names   = {}

	# Default config example
	default_config  = {'dbid': None,
	                   'name': None,
	                   'parser': None,
	                   'access': 'public'
	                  }


	def __init__ (self, db):
		self.db = db

		# Recover saved config files
		configs = self.db.getConfigs()
		for c in configs:
			configp = ConfigParser.ConfigParser()
			configp.readfp(StringIO.StringIO(str(c['config'])))
			self._parseConfig(configp=configp,
			                  pid=str(c['profile_id']),
			                  dbid=str(c['_id']))

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

	# Add (or re-add) the information in the config file to the stored maps
	def _parseConfig (self, configp, pid, dbid):
		config = copy.copy(self.default_config)

		try:
			main = configp.items('main')
			# Load in the general main settings
			for item in main:
				config[item[0]] = item[1]

		except ConfigParser.NoSectionError:
			print('ERROR: Unable to find section "main" in the config file.')
			raise FE.BadConfigFile('Missing main section')

		try:
			name = config['name']

			# Add a mapping of name to profile id so that when we read in
			# config files we can match them up.
			self.names[name] = pid
		except KeyError:
			print('ERROR: Unable to find "name" in main section')
			raise FE.BadConfigFile('Missing name')

		# Get the python filename for this package
		parser_name      = config['parser']
		parser           = self._getParser(parser_name=parser_name)
		config['parser'] = parser
		config['dbid']   = dbid

		if pid not in self.configs:
			print("Adding config {}: {}".format(name, pid))

		# Save the settings
		self.configs[pid] = config

		# Clear out the old addresses
		for ipaddr in self.addrs:
			if self.addrs[ipaddr] == pid:
				self.addrs[ipaddr] = None

		# Loop through all sources
		try:
			index = 0
			while True:
				source = configp.items('source{}'.format(index))
				for item in source:
					if item[0] == 'ipaddress':
						# Add the IP address to the dict
						self._addAddr(ip_str=item[1], pid=pid)
						break

				index += 1

		except ConfigParser.NoSectionError:
			pass



	# Parse and add a config file to the database if needed
	def addConfigFile (self, filename):
		try:
			configp = ConfigParser.ConfigParser()
			configp.read(filename)

			# Save the config file to a string that we can insert in the
			# database.
			str_ptr = StringIO.StringIO()
			configp.write(str_ptr)

			name = configp.get('main', 'name')
			if name in self.names:
				# Already have this config file, update it
				pid = self.names[name]
				dbid = self.configs[pid]['dbid']
				self.db.updateConfig(uid=dbid,
				                     name=name,
				                     config_file=str_ptr.getvalue(),
				                     profile_id=pid)

			else:
				# Get unique ID for this profile
				pid = self._createProfileId()

				# Store this configuration to get the unique id
				dbid = self.db.storeConfig(name=name,
				                           config_file=str_ptr.getvalue(),
				                           profile_id=pid)
				self.dbids[dbid] = pid


			# Now parse the file
			self._parseConfig(configp=configp, pid=pid, dbid=dbid)

		except ConfigParser.NoSectionError as e:
			print "Invalid config file. Missing " + str(e) + " in [main]."


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

		return r


