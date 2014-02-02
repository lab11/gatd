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
			self.mongo_db = self.mongo_conn[gatdConfig.mongo.DATABASE]
			self.mongo_db.authenticate(gatdConfig.mongo.USERNAME,
			                           gatdConfig.mongo.PASSWORD)
			self.stop = False

		except pymongo.errors.ConnectionFailure:
			print "Could not connect. Check the host and port."
			sys.exit(1)

	def get (self, query):

		# Use the capped collection to implement streaming starting at a time
		# in the past. If the time key is present it is used as the minimum
		# timestamp.
		now = int(round(time.time() * 1000))
		if 'time' in query:
			start = now - query['time']
		else:
			start = now
		query['time'] = {'$gt': start}

		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED_CAP].find(query,
			tailable=True,
			await_data=True)
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])
				yield n
			except StopIteration:
				pass


	def __del__ (self):
		self.mongo_conn.close()
