import os
import pymongo
import sys
import time

import gevent

sys.path.append(os.path.abspath('../config'))
import gatdConfig

class MongoInterface(gevent.greenlet.Greenlet):

	def __init__(self, cb, query):
		# Connect to the mongo database

		super(MongoInterface, self).__init__()

		try:
			from gevent import monkey
			monkey.patch_socket()
			self.mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
			                                      port=gatdConfig.mongo.PORT,
												  use_greenlets=True)
			self.mongo_db = self.mongo_conn[gatdConfig.mongo.DATABASE]
			self.mongo_db.authenticate(gatdConfig.mongo.USERNAME,
			                           gatdConfig.mongo.PASSWORD)
			self.stop = False

			self.cb = cb
			self.query = query
		except pymongo.errors.ConnectionFailure:
			print "Could not connect. Check the host and port."
			sys.exit(1)

	def run (self):

		# Use the capped collection to implement streaming starting at a time
		# in the past. If the time key is present it is used as the minimum
		# timestamp.
		now = int(round(time.time() * 1000))
		if 'time' in self.query:
			start = now - query['time']
		else:
			start = now
		self.query['time'] = {'$gt': start}

		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED_CAP].find(self.query,
			tailable=True,
			await_data=True)
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])
				self.cb('data', n)
			except StopIteration:
				pass

	def get_all (self, query):

		now = int(round(time.time() * 1000))
		if 'time' in query:
			start = now - query['time']
		else:
			start = now
		query['time'] = {'$gt': start}

		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED].find(query)
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])
				yield n
			except StopIteration:
				pass

	# Retrieve records from the main collection and replay them as if they
	# were coming in in real time
	def get_all_replay (self, query):
	
		speedup = 1.0
	
		if '_speedup' in query:
			speedup = float(query['_speedup'])
			del query['_speedup']

		# The user must provide the proper query
		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED].find(query)
		                                       #.sort('time', pymongo.ASCENDING)

		last_time = 0
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])


				if 'time' in n:
					if last_time == 0:
						yield n
					elif n['time'] < last_time:
						yield n
					else:
						time.sleep(((n['time'] - last_time)/1000.0)/speedup)
						yield n

					last_time = n['time']

				else:
					yield n
			except StopIteration:
				pass


	def __del__ (self):
		self.mongo_conn.close()
