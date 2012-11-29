import ConfigParser
import copy
import FormatterExceptions as FE
import IPy
#from pymongo import objectid
import random
import string
import StringIO
import sys
import uuid

class profileManager:

	# Map of package name->[uid, profile_id]
	# I'm using name as a unique identifier
	names    = {}

	# Map of ip addr->uid
	addrs    = {}

	# Map of profile id (not uid) -> uid
	pids     = {}

	# Worthless map because I'm lazy and don't feel like writing this differently
	info     = {}

	# Map of uid->settings map
	settings = {}

	# Default settings
	default  = {'name': None,
                'parser': None,
                'access': 'public'
	           }

	configp  = ConfigParser.ConfigParser()


	def __init__ (self, db):
		self.db = db

		# Recover saved config files
		configs = self.db.getConfigs()
		for c in configs:
			self._addMapInfo(name=str(c['name']),
			                 pid=str(c['profile_id']),
			                 uid=str(c['_id']))
	#		self._addProfileId(id=c['profile_id'], uid=str(c['_id']))
			self.configp = ConfigParser.ConfigParser()
			self.configp.readfp(StringIO.StringIO(str(c['config'])))
			self._parseConfig()

	def __str__ (self):
		out = 'addrs\n'
		for a in self.addrs:
			out += str(IPy.IP(a)) + ': ' + str(self.addrs[a]) + '\n'
		return out

	def _addAddr (self, ip_str, uid):
		# Add the IP address to the dict
		ip = IPy.IP(ip_str, ipversion=6)
		self.addrs[ip.int()] = uid

	def _addMapInfo (self, name, pid, uid):
		self.names[name] = [uid, pid]
		self.pids[pid]   = uid
		self.info[uid]   = pid

	def _createProfileId (self):
		id = ''.join(random.choice(string.letters + string.digits) for x in range(10))
		return id

	def _getParser (self, parser_name):
		# Load the python parser
		exec('import ' + parser_name)
		parser_mod = sys.modules[parser_name]
		parser_n   = getattr(parser_mod, parser_name)
		parser     = parser_n()

		# return the parser
		return parser

	# Add the information in the config file to the stored maps
	# The config file should be 'known' already, so the uid is known, etc.
	def _parseConfig (self):
		try:
			settings = copy.copy(self.default)
			main     = self.configp.items('main')

			# Load in the general main settings
			for item in main:
				settings[item[0]] = item[1]

	#		if 'name' not in settings or 'parser' not in settings:
	#			print 'Bad config file'
	#			return

			uid  = self.names[settings['name']][0]

	#		if name in self.names:
				# Already have this config file
	#			return
	#		else:
	#			self.names[name] = uid;

			# Get the python filename for this package
			parser_name        = settings['parser']
			parser             = self._getParser(parser_name=parser_name)
			settings['parser'] = parser

			# Save the settings
			self.settings[uid] = settings

			# Clear out the old addresses
			for ipaddr in self.addrs:
				if self.addrs[ipaddr] == uid:
					self.addrs[ipaddr] = None

			# Loop through all sources
			index = 0
			while True:
				source = self.configp.items('source' + str(index))
				ip_str = ''
				for item in source:
					if item[0] == 'ipaddress':
						ip_str = item[1]
						break
				# Add the IP address to the dict
				self._addAddr(ip_str=ip_str, uid=uid)

				index += 1

		except ConfigParser.NoSectionError:
			pass


	def addConfigFile (self, filename):
		uid          = None
		self.configp = ConfigParser.ConfigParser()

		try:
			self.configp.read(filename)

			str_ptr = StringIO.StringIO()
			self.configp.write(str_ptr)

			name = self.configp.get('main', 'name')
			if name in self.names:
				# Already have this config file, update it
				uid = self.names[name][0]
				pid = self.names[name][1]
				self.db.updateConfig(uid=uid,
				                     name=name,
				                     config_file=str_ptr.getvalue(),
				                     profile_id=pid)

			else:
				# Get unique ID for this profile
				pid = self._createProfileId()

				# Store this configuration to get the unique id
				uid = self.db.storeConfig(name=name,
				                          config_file=str_ptr.getvalue(),
				                          profile_id=pid)

				# Add it to the maps
				self._addMapInfo(name=name, uid=uid, pid=pid)


			# Now parse the file
			self._parseConfig()

		except ConfigParser.NoSectionError as e:
			print "Invalid config file. Missing " + str(e) + " in [main]."

	#	except Exception as e:
	#		print e
	#		sys.exit(1)

	def getPacketUid (self, addr, data):
		if addr != None:
			ip = IPy.IP(addr)
			if ip.int() in self.addrs:
				return self.addrs[ip.int()]

		if len(data) > 10:
			pid = data[0:10]
			if pid in self.pids:
				return self.pids[pid]

		return None

	# Check if an IP address of an incoming packet is recognized or not
	def isPacketKnown (self, data, meta):
		addr = meta['addr'] if ('addr' in meta) else None
		return self.getPacketUid(addr=addr, data=data) != None

	# Do the parse of the actual data packet
	# Returns a dict
	# Raises exception if parser is bad
	def parsePacket (self, data, meta):
		addr     = meta['addr'] if ('addr' in meta) else None
		uid      = self.getPacketUid(addr=addr, data=data)

		if uid == None:
			# Don't recognize this packet
			raise FE.ParserNotFound("No parser for this packet.")

		settings = self.settings[uid]
		parser   = settings['parser']
		pid      = self.info[uid]

		# Create dict of settings that need to get passed to parser
		psettings = {}

		try:
			if settings['access'] == 'public':
				psettings['public'] = True
		except KeyError:
			psettings['public'] = False


		# need to fill in extra at some point
		extra = {}

		try:
			r = parser.parse(data=data, meta=meta, extra=extra, settings=psettings)
			r['profile_id'] = pid
		except Exception as e:
			print "Bad Parser: " + str(e)
			r = None

		if type(r) != dict:
			raise FE.ParserError('Parser does not return a dict.')

		return r


