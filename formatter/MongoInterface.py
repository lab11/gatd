import pymongo
#import pymongo.objectid
import time
import bson


class MongoInterface:

	DATABASE          = 'getallthedata'
	TABLE_UNFORMATTED = 'unformatted_archive'
	TABLE_FORMATTED   = 'formatted_data'
	TABLE_CONFIG      = 'configuration'


	def __init__(self, host, port):
		# Connect to the mongo database
		try:
			self.mongo_conn = pymongo.Connection(host=host, port=port)
			self.mongo_db   = self.mongo_conn[self.DATABASE]
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
		id = self.mongo_db[self.TABLE_CONFIG].save(config_map)
		return str(id)

	def updateConfig (self, uid, name, config_file, profile_id):
		config_map = {'_id'       : bson.objectid.ObjectId(uid),
		              'name'      : name,
		              'config'    : config_file,
		              'profile_id': profile_id}
		self.mongo_db[self.TABLE_CONFIG].save(config_map)

	def getConfigs (self):
		configs = self.mongo_db[self.TABLE_CONFIG].find({})
		return list(configs)

	def getArchives (self):
		r = self.mongo_db[self.TABLE_UNFORMATTED].find()
		for i in r:
			yield i

	def deleteArchive (self, uid):
		self.mongo_db[self.TABLE_UNFORMATTED].remove({'_id': pymongo.objectid.ObjectId(uid)})

	"""
	# Manage Locations
	def hasLocation (self, address):
		return self.mongo_db.locations.find({'address':address}).count() > 0

	def addLocation (self, data):
		address = data['address']
		self.cur = self.mongo_db.locations.find({'address':address}, {'_id':0, 'address':0, 'timestamp':0}).limit(1).sort('_id', -1)
		location = self.cur.next()
		data.update(location)
		return data"""

	def __del__ (self):
		self.mongo_conn.close()

