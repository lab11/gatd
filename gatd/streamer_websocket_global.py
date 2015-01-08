#!/usr/bin/env python3

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
	def open(self, uuid):
		uuid = uuid.decode('utf-8')
		self.uuid = uuid

	def on_message(self, message):
		print('message received')
		print(message)

		db.conf_users.find().each(callback=self.on_packet)


	def on_close(self):
		print('connection closed')

	def on_packet(self, msg, err):
		if msg:
			msg['_id'] = str(msg['_id'])
			self.write_message(msg)



dbc = motor.MotorClient('mongodb://{host}:{port}'\
			.format(host=gatdConfig.mongo.HOST, port=gatdConfig.mongo.PORT)
		)
db = dbc[gatdConfig.mongo.DATABASE]
db.authenticate(username=gatdConfig.blocks.MDB_USERNAME,
				password=gatdConfig.blocks.MDB_PASSWORD)
# db = dbc[gatdConfig.mongo.DATABASE]

# print(db)

# def cb (a, b):
# 	print(a)
# 	print(b)
# db.collection_names(callback=cb)

# def a():
# 	print('doit')
# 	# d = yield db.conf_users.find_one({})
# 	# print(d)
# a()

# print(a)

application = tornado.web.Application([
	(r'/(.*)', WSHandler),
], db=db, debug=True)


# if __name__ == "__main__":
http_server = tornado.httpserver.HTTPServer(application)
http_server.listen(gatdConfig.streamer_websocket.PORT)

# application.listen(gatdConfig.streamer_websocket.PORT)
tornado.ioloop.IOLoop.instance().start()