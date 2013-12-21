from gevent import monkey; monkey.patch_all()

import gatdConfig
import MongoInterface
import pymongo
import socketio
import socketio.namespace
import socketio.server
import socketio.mixins

SOCKETIO_PYTHON_PORT = 8082


class socketioManager(object):

	def __call__(self, environ, start_response):
		socketio.socketio_manage(environ, {'/stream': socketioStreamer});

class socketioStreamer(socketio.namespace.BaseNamespace):
	def on_query(self, msg):
		self.m = MongoInterface.MongoInterface(host=gatdConfig.getMongoHost(),
                   port=gatdConfig.getMongoPort(),
                   username=gatdConfig.getMongoUsername(),
                   password=gatdConfig.getMongoPassword())
		for r in self.m.get(msg):
			self.emit('data', r)


socketio.server.SocketIOServer(('0.0.0.0', SOCKETIO_PYTHON_PORT),
                               socketioManager(),
                               resource="socket.io",
                               policy_server=False
                              ).serve_forever()
