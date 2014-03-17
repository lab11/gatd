#!/usr/bin/env python2

##
## Stream packets from the past as if they were coming in now
##  "replay" them.
##

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
		print('got query {}'.format(msg))
		for r in self.m.get_all_replay(msg):
			self.emit('data', r)
		print('out of itesms')
		self.disconnect()

socketio.server.SocketIOServer(('0.0.0.0', gatdConfig.socketio.PORT_PYTHON_REPLAY),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
