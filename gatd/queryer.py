#!/usr/bin/env python3

import base64
import json

import bson
import bson.json_util
import flask
import pymongo

import gatdConfig
import gatdLog
l = gatdLog.getLogger('queryer')

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
	global l
	flask.g.db = connect_mongodb()
	flask.g.l = l

@app.route('/<uuid>', methods=['GET', 'POST'])
def viewer (uuid):

	d = flask.g.db['conf_virtual_queues'].find_one({'uuid': uuid})

	if d and ('source_uuids' in d) and (len(d['source_uuids'])):
		# Valid UUID to query with valid DB attached

		format = flask.request.args.get('format', 'json')

		if flask.request.method == 'POST':
			if len(flask.request.data) == 0:
				query = {}
			else:
				try:
					query = json.loads(flask.request.data.decode('utf-8'))
				except:
					r = {'status': 'error',
					     'msg': 'Could not parse the POST query as JSON.'}
					return flask.Response(json.dumps(r),  mimetype='application/json')

		else:
			query = flask.request.args.get('query', None)
			if not query:
				query = {}
			else:
				try:
					query = base64.b64decode(query)
				except:
					r = {'status': 'error',
					     'msg': 'Could not parse the GET query parameter as base64.'}
					return flask.Response(json.dumps(r),  mimetype='application/json')
				try:
					query = json.loads(query.decode('utf-8'))
				except:
					r = {'status': 'error',
					     'msg': 'Could not parse the GET query parameter as json.'}
					return flask.Response(json.dumps(r),  mimetype='application/json')

		flask.g.l.debug('query: {}'.format(query))


		if format == 'json':
			# Return JSON

			l = list(flask.g.db[d['source_uuids'][0]].find(query))
			for i in l:
				i['_id'] = str(i['_id'])

			return flask.Response(json.dumps(l),  mimetype='application/json')

		elif format == 'file':
			# Return JSON in a file

			r = flask.g.db[d['source_uuids'][0]].find(query)

			def generate(items):
				for i in items:
					yield '{}\n'.format(bson.json_util.dumps(i))

			resp = flask.Response(generate(r),
			                      mimetype='application/json',
			                      headers={
			                        'Content-Disposition': 'attachment; filename=data.json'
			                      })
			return resp

		elif format == 'bson':
			# Return BSON in a file

			r = flask.g.db[d['source_uuids'][0]].find(query)

			def generate(items):
				b = bson.BSON()
				for i in items:
					yield bytes(b.encode(i))

			resp = flask.Response(generate(r),
			                      mimetype='application/octet-stream',
			                      headers={
			                        'Content-Disposition': 'attachment; filename=data.bson',
			                        'Content-Transfer-Encoding': 'binary'
			                      })
			return resp

		else:
			r = {'status': 'error',
			     'msg': 'Unknown format.'}
			return flask.Response(json.dumps(r),  mimetype='application/json')

	else:
		r = {'status': 'error',
		     'msg': 'Viewer not properly connected to a database.'}
		return flask.Response(json.dumps(r),  mimetype='application/json')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=gatdConfig.queryer.PORT)
