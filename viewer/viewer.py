#!/usr/bin/env python2

import base64
import glob
import json
import os
import pymongo
import setproctitle
import sys
import tornado.ioloop
import tornado.web
import tornado
import time

sys.path.append(os.path.abspath('../config'))
sys.path.append(os.path.abspath('../formatter'))
import gatdConfig


def mongo_connect ():
	mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
			                         port=gatdConfig.mongo.PORT)
	mongo_db = mongo_conn[gatdConfig.mongo.DATABASE]
	mongo_db.authenticate(gatdConfig.mongo.USERNAME,
				          gatdConfig.mongo.PASSWORD)
	return mongo_db

class ViewerBaseHandler (tornado.web.RequestHandler):
	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")

class RecentViewerRequestHandler (ViewerBaseHandler):
	def get (self, pid):
		self.set_header('Content-Type', 'application/json')

		arg_time = self.get_argument('time', None)
		arg_limit = self.get_argument('limit', None)
		if arg_limit:
			arg_limit = int(arg_limit)
		arg_query = self.get_argument('query', None)

		query = {'profile_id': pid}

		if arg_time:
			now = int(round(time.time() * 1000))
			start = now - int(arg_time)
			query['time'] = {'$gt': start}

		if arg_query:
			query.update(json.loads(base64.b64decode(arg_query)))

		mdb = mongo_connect()

		mcur = mdb[gatdConfig.mongo.COL_FORMATTED_CAPPED]\
			          .find(query)\
			          .sort([('time', pymongo.ASCENDING)])
		if (arg_limit):
			mcur = mcur.sort([('time', pymongo.DESCENDING)]).limit(arg_limit)

		res = list(mcur)

		if arg_limit:
			# Need to reverse the list because we sorted it backwards
			# to make limit work
			res = list(reversed(res))

		for r in res:
			r['_id'] = str(r['_id'])

		self.write(json.dumps(res))

# Make this python instance recognizable in top
setproctitle.setproctitle('gatd-viewer')

t = tornado.web.Application([
	(r"/viewer/recent/([a-zA-Z0-9]{10})", RecentViewerRequestHandler),
], debug=True)
t.listen(gatdConfig.viewer.PORT)

# Run the loop!
tornado.autoreload.start()
tornado.ioloop.IOLoop.instance().start()
