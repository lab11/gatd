#!/usr/bin/env python3

"""
Handles the HTTP requests for the viewer.
"""

import json

import flask
import pymongo

import gatdConfig
import gatdLog

l = gatdLog.getLogger('viewer-global')

app = flask.Flask(__name__)

def connect_mongodb ():
	# get a mongo connection
	mc = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
	                         port=gatdConfig.mongo.PORT)
	mdb = mc['gatdv6']
	mdb.authenticate(gatdConfig.blocks.MDB_USERNAME,
	                 gatdConfig.blocks.MDB_PASSWORD)

	return mdb

@app.before_request
def before_request ():
	flask.g.db = connect_mongodb()

@app.route('/<uuid>')
def viewer (uuid):

	d = flask.g.db['viewer'].find_one({'uuid': uuid})
	if d:

		count = int(flask.request.args.get('count', 10))

		end = len(d['packets'])
		start = end - count
		if start < 0:
			start = 0

		resp = d['packets'][start:end]

	else:
		resp = {}

	return flask.Response(json.dumps(resp),  mimetype='application/json')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=gatdConfig.viewer.PORT)
