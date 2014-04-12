import os
import pymongo
import sys
import time

from gevent import monkey
monkey.patch_socket()
import gevent

sys.path.append(os.path.abspath('../config'))
import gatdConfig

class MongoInterface(gevent.greenlet.Greenlet):

	def __init__(self, cb, cmd, done_cb):
		# Connect to the mongo database

		gevent.greenlet.Greenlet.__init__(self)

		try:
			self.mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
			                                      port=gatdConfig.mongo.PORT,
												  use_greenlets=True)
			self.mongo_db = self.mongo_conn[gatdConfig.mongo.DATABASE]
			self.mongo_db.authenticate(gatdConfig.mongo.USERNAME,
			                           gatdConfig.mongo.PASSWORD)
			self.stop = False

			# Save the emit() function used to send the data packet
			self.cb = cb

			# The function to call when all packets have been found
			self.done = done_cb

			# Configure which streamer we actually want to use
			if cmd == 'get_new':
				self.cmd = self._get_new
			elif cmd == 'get_all':
				self.cmd = self._get_all
			elif cmd == 'get_all_replay':
				self.cmd = self._get_all_replay

		except pymongo.errors.ConnectionFailure:
			print "Could not connect. Check the host and port."
			sys.exit(1)

	def set_query (self, query):
		self.query = query

	def run (self):
		self.stop = False
		(self.cmd)()

	def _get_new (self):
		try:
			# Use the capped collection to implement streaming starting at a
			# time in the past. If the time key is present it is used as the
			# minimum timestamp.
			now = int(round(time.time() * 1000))
			if 'time' in self.query:
				start = now - self.query['time']
			else:
				start = now
			self.query['time'] = {'$gt': start}

			cursor = self.mongo_db[gatdConfig.mongo.COL_FORMATTED_CAP].find(
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
			pass

	def _get_all (self):
		try:
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
					yield n
				except StopIteration:
					pass
			(self.done)()
		except gevent.greenlet.GreenletExit:
			pass

	# Retrieve records from the main collection and replay them as if they
	# were coming in in real time
	def _get_all_replay (self):
		try:
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
			(self.done)()
		except gevent.greenlet.GreenletExit:
			pass


	def __del__ (self):
		self.mongo_conn.close()
