import pymongo
import time
import bson


class MongoInterface:

	TABLE_FORMATTED_CAP = 'formatted_data_capped'


	def __init__(self, host, port, username=None, password=None):
		# Connect to the mongo database
		try:
			self.mongo_conn = pymongo.MongoClient(host=host, port=port)
			self.mongo_db   = self.mongo_conn[self.DATABASE]
			if username:
				self.mongo_db.authenticate(username, password)
			self.stop = False

		except pymongo.errors.ConnectionFailure as e_cf:
			print "Could not connect. Check the host and port."
			exit(1)

	def get (self, query):

		# We are only streaming out of the tailable capped collection
		# Make sure we only get packets from now onward
		now = int(round(time.time() * 1000))
		query['time'] = {'$gt': now}

		cursor = self.mongo_db[self.TABLE_FORMATTED_CAP].find(query,
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


if __name__ == '__main__':
	MONGO_HOST  = 'inductor.eecs.umich.edu'
	MONGO_PORT  = 19000
	m = MongoInterface(MONGO_HOST, MONGO_PORT)
