#!/usr/bin/env python3

"""
Stream data with just websockets.
"""

import json

import motor
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import tornado.gen

import gatdConfig
import gatdLog

l = gatdLog.getLogger('streamer-websocket')

class WSHandler(tornado.websocket.WebSocketHandler):

	@tornado.web.asynchronous
	@tornado.gen.engine
	def open (self, uuid):
		#uuid = uuid.decode('utf-8')
		self.uuid = uuid
		l.debug('Got connection with {}'.format(uuid))

	def on_message (self, message):
		query = json.loads(message)
		l.debug('Got query {}'.format(query))

		db[self.uuid].find(
			query,
			tailable=True,
			await_data=True).each(callback=self.on_packet)


	# def on_close(self):
	# 	print('connection closed')

	def on_packet (self, msg, err):
		if msg:
			msg['_id'] = str(msg['_id'])
			self.write_message(msg)


dbc = motor.MotorClient('mongodb://{host}:{port}'\
			.format(host=gatdConfig.mongo.HOST, port=gatdConfig.mongo.PORT)
		)
db = dbc[gatdConfig.mongo.DATABASE]
db.authenticate(username=gatdConfig.blocks.MDB_USERNAME,
				password=gatdConfig.blocks.MDB_PASSWORD)


application = tornado.web.Application([
	(r'/(.*)', WSHandler),
], db=db, debug=True)

http_server = tornado.httpserver.HTTPServer(application)
http_server.listen(gatdConfig.streamer_websocket.PORT)
#application.listen(gatdConfig.streamer_websocket.PORT)
tornado.ioloop.IOLoop.instance().start()
