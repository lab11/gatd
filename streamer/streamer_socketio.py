#!/usr/bin/env python2


import sys
import os
import pymongo
import socketio
import socketio.namespace
import socketio.server
import socketio.mixins

import setproctitle

sys.path.append(os.path.abspath('../config'))
import gatdConfig
import MongoInterface

class socketioManager(object):

	def __call__(self, environ, start_response):
		socketio.socketio_manage(environ,
			{gatdConfig.socketio.STREAM_PREFIX: socketioStreamer});

class socketioStreamer(socketio.namespace.BaseNamespace):
	def recv_connect (self):
		pass

	def on_query (self, msg):
		print(msg)
		self.msg  = msg
		m = MongoInterface.MongoInterface(self.emit, self.disconnect)
		m.set_query(msg)

		# Configure which streamer we actually want to use
		if cmd == 'get_new':
			self.spawn(m.get_new)
		elif cmd == 'get_all':
			self.spawn(m.get_all)
		elif cmd == 'get_all_replay':
			self.spawn(m.get_all_replay)

	def recv_disconnect (self):
		print('disconnect: {}'.format(self.msg))
		pass


# Configure which streamer based on command line argument
if len(sys.argv) != 2:
	print('usage: {} new|all|replay'.format(sys.argv[0]))
	sys.exit(1)

if sys.argv[1] == 'new':
	setproctitle.setproctitle('gatd-s: sio-base')
	cmd = 'get_new'
	port = gatdConfig.socketio.PORT_PYTHON
elif sys.argv[1] == 'all':
	setproctitle.setproctitle('gatd-s: sio-hist')
	cmd = 'get_all'
	port = gatdConfig.socketio.PORT_PYTHON_HISTORICAL
elif sys.argv[1] == 'replay':
	setproctitle.setproctitle('gatd-s: sio-repl')
	cmd = 'get_all_replay'
	port = gatdConfig.socketio.PORT_PYTHON_REPLAY
else:
	print('usage: {} new|all|replay'.format(sys.argv[0]))
	sys.exit(1)


socketio.server.SocketIOServer(('0.0.0.0', port),
                               socketioManager(),
                               resource='socket.io',
                               policy_server=False
                              ).serve_forever()
