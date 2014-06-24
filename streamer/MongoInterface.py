import os
import pymongo
import sys
import time

from gevent import monkey
monkey.patch_socket()
import gevent

sys.path.append(os.path.abspath('../config'))
import gatdConfig

class MongoInterface ():

	def __init__ (self, cb, done_cb):

		# Connect to the mongo database
		while True:
			try:
				self._connect_mongo()
				break
			except pymongo.errors.ConnectionFailure:
				print("Could not connect. Check the host and port.")
				print("Retrying")

		self.stop = False

		# Save the emit() function used to send the data packet
		self.cb = cb

		# The function to call when all packets have been found
		self.done = done_cb

	def set_query (self, query):
		self.query = query

	def _connect_mongo (self):
		self.mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
		                                      port=gatdConfig.mongo.PORT,
		                                      use_greenlets=True)
		self.mongo_db = self.mongo_conn[gatdConfig.mongo.DATABASE]
		self.mongo_db.authenticate(gatdConfig.mongo.USERNAME,
		                           gatdConfig.mongo.PASSWORD)

	def get_new (self):
		# Use the capped collection to implement streaming starting at a
		# time in the past. If the time key is present it is used as the
		# minimum timestamp.
		now = int(round(time.time() * 1000))
		if 'time' in self.query:
			start = now - self.query['time']
		else:
			start = now
		self.query['time'] = {'$gt': start}
		
		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED_CAPPED].find(
			self.query,
			tailable=True,
			await_data=True)
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])
				self.cb('data', n)
			except StopIteration:
				pass
			except gevent.greenlet.GreenletExit:
				self.mongo_conn.close()
				return

	def get_all (self):
		now = int(round(time.time() * 1000))
		if 'time' in self.query:
			start = now - self.query['time']
		else:
			start = now
		self.query['time'] = {'$gt': start}

		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED].find(
			self.query)
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])
				self.cb('data', n)
			except StopIteration:
				pass
			except gevent.greenlet.GreenletExit:
				self.mongo_conn.close()
				return

		# Call the disconnect function at the end
		(self.done)()

	# Retrieve records from the main collection and replay them as if they
	# were coming in in real time
	def get_all_replay (self):
		speedup = 1.0

		if '_speedup' in self.query:
			speedup = float(self.query['_speedup'])
			del self.query['_speedup']

		# The user must provide the proper query
		cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED].find(self.query)
		                                   #.sort('time', pymongo.ASCENDING)

		last_time = 0
		while cursor.alive and not self.stop:
			try:
				n = cursor.next()
				n['_id'] = str(n['_id'])


				if 'time' in n:
					if last_time == 0:
						self.cb('data', n)
					elif n['time'] < last_time:
						self.cb('data', n)
					else:
						time.sleep(((n['time'] - last_time)/1000.0)/speedup)
						self.cb('data', n)

					last_time = n['time']
				else:
					self.cb('data', n)
			except StopIteration:
				pass
			except gevent.greenlet.GreenletExit:
				self.mongo_conn.close()
				return

		# Signal disconnect
		(self.done)()

