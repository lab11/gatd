#!/usr/bin/env python2


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

		self.m = MongoInterface.MongoInterface(self.emit, cmd, self.disconnect)
		self.m.set_query(msg)
		self.m.start()

	def recv_disconnect (self):
		self.m.kill(timeout=1)
		del self.m


# Configure which streamer based on command line argument
if len(sys.argv) != 2:
	print('usage: {} new|all|replay'.format(sys.argv[0]))
	sys.exit(1)

if sys.argv[1] == 'new':
	cmd = 'get_new'
	port = gatdConfig.socketio.PORT_PYTHON
elif sys.argv[1] == 'all':
	cmd = 'get_all'
	port = gatdConfig.socketio.PORT_PYTHON_HISTORICAL
elif sys.argv[1] == 'replay':
	cmd = 'get_all_replay'
	gatdConfig.socketio.PORT_PYTHON_REPLAY
else:
	print('usage: {} new|all|replay'.format(sys.argv[0]))
	sys.exit(1)


socketio.server.SocketIOServer(('0.0.0.0', port),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
