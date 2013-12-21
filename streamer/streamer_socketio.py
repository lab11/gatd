from gevent import monkey; monkey.patch_all()

import sys
import os
import pymongo
import socketio
import socketio.namespace
import socketio.server
import socketio.mixins

sys.path.append(os.path.abspath('../config'))
import gatdConfig
import MongoInterface

class socketioManager(object):

	def __call__(self, environ, start_response):
		socketio.socketio_manage(environ,
			{gatdConfig.socketio.STREAM_PREFIX: socketioStreamer});

class socketioStreamer(socketio.namespace.BaseNamespace):
	def on_query(self, msg):
		self.m = MongoInterface.MongoInterface()
		for r in self.m.get(msg):
			self.emit('data', r)


socketio.server.SocketIOServer(('0.0.0.0', gatdConfig.socketio.PORT_PYTHON),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
