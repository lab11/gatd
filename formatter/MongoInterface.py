import bson
import IPy
import os
import pymongo
import sys
import time

sys.path.append(os.path.abspath('../config'))
import gatdConfig


class MongoInterface:

	def __init__(self):
		# Connect to the mongo database
		try:
			self.mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
			                                      port=gatdConfig.mongo.PORT)
			self.mongo_db   = self.mongo_conn[gatdConfig.mongo.DATABASE]
			if gatdConfig.mongo.USERNAME:
				self.mongo_db.authenticate(gatdConfig.mongo.USERNAME,
				                           gatdConfig.mongo.PASSWORD)
			self.cur        = None
			self.skip       = 0

		except pymongo.errors.ConnectionFailure as e_cf:
			print "Could not connect. Check the host and port."
			sys.exit(1)

	# Write to unformatted archive table
	def writeUnformatted (self, to_write):
		try:
			self.mongo_db[gatdConfig.mongo.COL_UNFORMATTED].save(to_write)
		except OverflowError as oe:
			print oe

	# Write data to the formatted data table
	# Also send it to the capped table that we use for streaming.
	def writeFormatted (self, to_write):
		try:
			self.mongo_db[gatdConfig.mongo.COL_FORMATTED].save(to_write)
			self.mongo_db[gatdConfig.mongo.COL_FORMATTED_CAPPED].save(to_write)
		except OverflowError as oe:
			print oe

	def addProfile (self, parser_name, profile_id, meta):
		config_map = {'parser_name': parser_name,
		              'profile_id' : profile_id}
		config_map.update(meta)
		uid = self.mongo_db[gatdConfig.mongo.COL_CONFIG].insert(config_map)
		return str(uid)

	def updateProfile (self, dbinfo, meta):
		config_map = {}
		config_map.update(dbinfo)
		config_map['_id'] = bson.objectid.ObjectId(dbinfo['_id'])
		config_map.update(meta)
		uid = self.mongo_db[gatdConfig.mongo.COL_CONFIG].save(config_map)
		return str(uid)

	def getProfileByParser (self, parser_name):
		return self.mongo_db[gatdConfig.mongo.COL_CONFIG].find_one(
			{'parser_name': parser_name})

	def getProfileByProfileId (self, pid):
		return self.mongo_db[gatdConfig.mongo.COL_CONFIG].find_one(
			{'profile_id': pid})

	def getAllProfiles (self):
		return list(self.mongo_db[gatdConfig.mongo.COL_CONFIG].find())

	# Each profile has its own key that has to be in the data packet in order
	# to add meta data. This is stored in the TABLE_META_CONFIG table.
	def getMetaRequiredKey (self, pid):
		mc = self.mongo_db[gatdConfig.mongo.COL_META_CONFIG].find_one(
			{'profile_id':pid})
		if mc == None:
			return None
		return mc['required_key']

	def setMetaRequiredKey (self, pid, req_key):
		insert = {'profile_id': pid,
		          'required_key': req_key}
		self.mongo_db[gatdConfig.mongo.COL_META_CONFIG].insert(insert)

	# Get the meta data associated with this packet
	def getMeta (self, pkt):
		pid = pkt['profile_id']

		req_key = self.getMetaRequiredKey(pid)
		if req_key == None:
			return {}

		try:
			req_key_value = pkt[req_key]
		except KeyError:
			# This packet doesn't have the required key so we skip this
			return {}

		# Get possible meta values
		metas = self.mongo_db[gatdConfig.mongo.COL_META].find({'profile_id':pid,
		                                            req_key:str(req_key_value)})

		meta = {}
		for m in metas:
			try:
				# Check that the query matches the incoming packet
				for query_key in m['query']:
					if pkt[query_key] != m['query'][query_key]:
						break
				else:
					meta.update(m['additional'])
			except KeyError:
				pass

		return meta

	def getRawMeta (self, pid):
		'''Return a list of dicts of all of the meta items in the collection
		for a given profile id'''
		metas = self.mongo_db[gatdConfig.mongo.COL_META].find({'profile_id':pid})
		req_key = self.getMetaRequiredKey(pid)
		if req_key == None:
			return []
		metas.sort(req_key, 1)
		return list(metas)

	def addMeta (self, pid, req_key, req_key_value, query, additional):
		insert = {'profile_id': pid,
		          req_key: req_key_value,
		          'query': query,
		          'additional': additional}
		self.mongo_db[gatdConfig.mongo.COL_META].insert(insert)

	def updateMeta (self, dbid, pid, req_key, req_key_value, query, additional):
		insert = {'_id':        bson.objectid.ObjectId(dbid),
		          'profile_id': pid,
		          req_key:      req_key_value,
		          'query':      query,
		          'additional': additional}
		self.mongo_db[gatdConfig.mongo.COL_META].save(insert)

	def deleteMeta (self, dbid):
		self.mongo_db[gatdConfig.mongo.COL_META].remove(
			{'_id': bson.objectid.ObjectId(dbid)})

	def getGatewayKeys (self, prefix):
		'''Return the key,value pairs that should be added to a packet that
		came though a gateway with this prefix.'''
		ret = {}
		query = {'prefix': str(prefix)}
		gateway = self.mongo_db[gatdConfig.mongo.COL_GATEWAY].find(query)
		for g in gateway:
			if 'additional' in g:
				ret.update(g['additional'])
		return ret

	def getRawGatewayKeys (self):
		gws = self.mongo_db[gatdConfig.mongo.COL_GATEWAY].find()
		gws.sort('prefix_cidr', 1)
		return list(gws)

	def addGatewayKeys (self, prefix, additional):
		'''Add a prefix for a gateway and associated additional keys to the
		collection.

		prefix: 64 bit number representing the upper 64 bits of the IP addr
		additional: dict of key,values to add to incoming packets'''
		prefix_ip = IPy.IP(prefix<<64)
		prefix_str = '{}/64'.format(prefix_ip)
		insert = {'prefix':      str(prefix),
		          'prefix_cidr': prefix_str,
		          'additional':  additional}
		self.mongo_db[gatdConfig.mongo.COL_GATEWAY].insert(insert)

	def updateGatewayKeys (self, dbid, prefix, additional):
		'''Same as addGatewayKeys but update an existing record'''
		prefix_str = '{}/64'.format(IPy.IP(prefix<<64))
		update = {'_id':         bson.objectid.ObjectId(dbid),
		          'prefix':      str(prefix),
		          'prefix_cidr': prefix_str,
		          'additional':  additional}
		self.mongo_db[gatdConfig.mongo.COL_GATEWAY].save(update)

	def deleteGatewayKeys (self, dbid):
		self.mongo_db[gatdConfig.mongo.COL_GATEWAY].remove(
			{'_id': bson.objectid.ObjectId(dbid)})

	def getExploreKeys (self):
		'''Return all of the data about which keys to use for exploratory
		discovery'''
		return list(self.mongo_db[gatdConfig.mongo.COL_EXPLORE_KEYS].find())

	def getExploreKeysSingle (self, pid):
		'''Return all of the data about which keys to use for exploratory
		discovery for a particular profile'''
		return self.mongo_db[gatdConfig.mongo.COL_EXPLORE_KEYS].find_one(
			{'profile_id': pid})

	def addExploreKeys (self, pid, keys_json):
		insert = {'profile_id': pid,
		          'keys_json': keys_json}
		self.mongo_db[gatdConfig.mongo.COL_EXPLORE_KEYS].insert(insert)

	def updateExploreKeys (self, dbid, pid, keys_json):
		insert = {'_id':        bson.objectid.ObjectId(dbid),
		          'profile_id': pid,
		          'keys_json': keys_json}
		self.mongo_db[gatdConfig.mongo.COL_EXPLORE_KEYS].save(insert)


	def getArchives (self):
		r = self.mongo_db[gatdConfig.mongo.COL_UNFORMATTED].find()
		for i in r:
			yield i

	def deleteArchive (self, uid):
		self.mongo_db[gatdConfig.mongo.COL_UNFORMATTED].remove(
			{'_id': pymongo.objectid.ObjectId(uid)})

	def __del__ (self):
		self.mongo_conn.close()
