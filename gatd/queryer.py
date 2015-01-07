import json

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
	flask.g.db = connect_mongodb()

@app.route('/<uuid>')
def viewer (uuid):

	d = flask.g.db['conf_virtual_queues'].find_one({'uuid': uuid})

	if d and ('source_uuids' in d) and (len(d['source_uuids'])):
		# Valid UUID to query with valid DB attached

		format = flask.request.args.get('format', 'json')

		if format == 'json':

			l = list(flask.g.db[d['source_uuids'][0]].find())
			for i in l:
				i['_id'] = str(i['_id'])

			return flask.Response(json.dumps(l),  mimetype='application/json')

	else:
		r = {'status': 'error',
		     'msg': 'Viewer not properly connected to a database.'}
		return flask.Response(json.dumps(r),  mimetype='application/json')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=gatdConfig.queryer.PORT)