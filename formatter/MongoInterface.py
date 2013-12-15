import pymongo
import time
import bson


class MongoInterface:

	DATABASE          = 'getallthedata'
	TABLE_UNFORMATTED = 'unformatted_archive'
	TABLE_FORMATTED   = 'formatted_data'
	TABLE_CONFIG      = 'configuration'
	TABLE_META_CONFIG = 'meta_config'
	TABLE_META        = 'meta'


	def __init__(self, host, port, username=None, password=None):
		# Connect to the mongo database
		try:
			self.mongo_conn = pymongo.MongoClient(host=host, port=port)
			self.mongo_db   = self.mongo_conn[self.DATABASE]
			if username:
				self.mongo_db.authenticate(username, password)
			self.cur        = None

			self.skip       = 0

		except pymongo.errors.ConnectionFailure as e_cf:
			print "Could not connect. Check the host and port."
			exit(1)

	# Write to unformatted archive table
	def writeUnformatted (self, to_write):
		try:
			self.mongo_db[self.TABLE_UNFORMATTED].save(to_write)
		except OverflowError as oe:
			print oe

	# Write data to the formatted data table
	def writeFormatted (self, to_write):
		try:
			self.mongo_db[self.TABLE_FORMATTED].save(to_write)
		except OverflowError as oe:
			print oe

	def storeConfig (self, name, config_file, profile_id):
		config_map = {'name'      : name,
		              'config'    : config_file,
		              'profile_id': profile_id}
		uid = self.mongo_db[self.TABLE_CONFIG].save(config_map)
		return str(uid)

	def updateConfig (self, uid, name, config_file, profile_id):
		config_map = {'_id'       : bson.objectid.ObjectId(uid),
		              'name'      : name,
		              'config'    : config_file,
		              'profile_id': profile_id}
		self.mongo_db[self.TABLE_CONFIG].save(config_map)

	def getConfigs (self):
		configs = self.mongo_db[self.TABLE_CONFIG].find({})
		return list(configs)

	# Each profile has its own key that has to be in the data packet in order
	# to add meta data. This is stored in the TABLE_META_CONFIG table.
	def getMetaRequiredKey (self, pid):
		mc = self.mongo_db[self.TABLE_META_CONFIG].find_one({'profile_id':pid})
		if mc == None:
			return None
		return mc['required_key']

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
		metas = self.mongo_db[self.TABLE_META].find({'profile_id':pid,
		                                             req_key:req_key_value})

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
		return list(self.mongo_db[self.TABLE_META].find({'profile_id':pid}))

	def getArchives (self):
		r = self.mongo_db[self.TABLE_UNFORMATTED].find()
		for i in r:
			yield i

	def deleteArchive (self, uid):
		self.mongo_db[self.TABLE_UNFORMATTED].remove(
			{'_id': pymongo.objectid.ObjectId(uid)})

	def __del__ (self):
		self.mongo_conn.close()


if __name__ == '__main__':
	MONGO_HOST  = 'inductor.eecs.umich.edu'
	MONGO_PORT  = 19000
	m = MongoInterface(MONGO_HOST, MONGO_PORT)
	print(m.getMetaRequiredKey("7aiOPJapXF"))
	print(m.getMetaRequiredKey("abc"))

	print('Test meta')
	test1 = {'profile_id':'7aiOPJapXF',
			'ccid':'1',
			'color':'blue'}
	test2 = {'profile_id':'7aiOPJapXF',
			'ccid':'1',
			'color':'red'}
	test3 = {'profile_id':'7aiOPJapXF',
			'ccid':'2',
			'color':'blue'}
	test4 = {'profile_id':'7aiOPJapXF',
			'ccid':'1',
			'colorer':'blue'}
	test5 = {'profile_id':'7aiOPJapXF',
			'ccid':'1',
			'color':'green'}
	test6 = {'profile_id':'7aiOPJapXF',
			'ccid':'1',
			'color':'green',
			'type':'new'}
	print('adding: {}'.format(m.getMeta(test1)))
	print('adding: {}'.format(m.getMeta(test2)))
	print('adding: {}'.format(m.getMeta(test3)))
	print('adding: {}'.format(m.getMeta(test4)))
	print('adding: {}'.format(m.getMeta(test5)))
	print('adding: {}'.format(m.getMeta(test6)))


