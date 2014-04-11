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
import MongoInterfaceDux

class socketioManager(object):

	def __call__(self, environ, start_response):
		socketio.socketio_manage(environ,
			{gatdConfig.socketio.STREAM_PREFIX: socketioStreamer});

class socketioStreamer(socketio.namespace.BaseNamespace):
	def on_query(self, msg):
		print(msg)
		self.m = MongoInterfaceDux.MongoInterface(self.emit, msg)
		self.m.start()
#		for r in self.m.get(msg):
#			self.emit('data', r)
#		while True:
#			self.emit('data', '{"k":"v"}')
#			print('emit k:v')
#			gevent.sleep(2)
#		self.emit("{}")

	def recv_disconnect (self):
		print('GOT DIS')


socketio.server.SocketIOServer(('0.0.0.0', 8086),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
