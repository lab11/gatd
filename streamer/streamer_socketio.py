#!/usr/bin/env python2

#from gevent import monkey; monkey.patch_all()
#import gevent

import sys
import os
import pymongo
import socketio
import socketio.namespace
import socketio.server
import socketio.mixins

import setproctitle
setproctitle.setproctitle('gatd-s: socketio')

sys.path.append(os.path.abspath('../config'))
import gatdConfig
import MongoInterface

class socketioManager(object):

	def __call__(self, environ, start_response):
		socketio.socketio_manage(environ,
			{gatdConfig.socketio.STREAM_PREFIX: socketioStreamer});

class socketioStreamer(socketio.namespace.BaseNamespace):
	def recv_connect (self):
		self.m = None

	def on_query (self, msg):
		if self.m:
			self.m.kill(timeout=1)

		self.m = MongoInterface.MongoInterface(self.emit, 'get_new')
		self.m.set_query(msg)
		self.m.start()

	def recv_disconnect (self):
		del self.m


socketio.server.SocketIOServer(('0.0.0.0', 8086),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
