
import bson
import json
import functools
import os
import resource
import signal
import socket
import struct
import sys
import time

import tornado
import cffi
import prctl

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-python')

_ffi = cffi.FFI()
_ffi.cdef('void _exit(int);')
_libc = _ffi.dlopen(None)


def _exit(n=1):
	"""Invoke _exit(2) system call."""
	_libc._exit(n)

def read_exact(fp, n):
	buf = b''
	while len(buf) < n:
		try:
			buf2 = os.read(fp.fileno(), n)
			if not buf2:
				print('child died')
				_exit(123)
		except:
			buf2 = b''

		buf += buf2
	return buf

def write_exact(fp, s):
	done = 0
	while done < len(s):
		written = os.write(fp.fileno(), s[done:])
		if not written:
			_exit(123)
		done += written



def init (args):
	pass





code = '''
def format_packet (data, meta):
	pkt = json.loads(data)
	print(pkt)
	pkt['query'] += 1
	return pkt
'''








host, child = socket.socketpair()

pid = os.fork()

if not pid:
	# Child process

	host.close()

	# Close file descriptors except for stdout and the one
	# that talks to the parent process
	for fd in map(int, os.listdir('/proc/self/fd')):
		if fd != child.fileno() and fd != 1:
			try:
				os.close(fd)
			except OSError:
				pass

	# Set limit and drop to seccomp mode
	resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
	prctl.set_seccomp(True)

	b = bson.BSON()

	# Load the unsafe code
	try:
		exec(code, globals())
	except:
		print('Code is not valid and did not exec() properly.')
		_exit(2)

	while True:
		sz, = struct.unpack('>L', read_exact(child, 4))
		data = read_exact(child, sz)
		pkt = bson.BSON.decode(data)

		try:
			response = format_packet(pkt['data'], pkt['meta'])
			print('Managed to format the packet')
			ret = b.encode(response)
			write_exact(child, struct.pack('>L', len(ret)))
			write_exact(child, ret)
			print('wrote response to parent')

		except:
			print('Format failed')
			ret = b'\x00'
			write_exact(child, struct.pack('>L', len(ret)))
			write_exact(child, ret)


else:
	# Parent process
	child.close()

	done_callback = None

	def write_to_sandbox (cb, data, meta):
		global done_callback
		done_callback = cb

		# Put the packet in a blob we can send to the sandbox
		b = bson.BSON()
		pkt = {'data': data,
		       'meta': meta}
		msg = b.encode(pkt)
		write_exact(host, struct.pack('>L', len(msg)))
		write_exact(host, msg)

	def read_from_sandbox (host_socket, fd, events):
		sz, = struct.unpack('>L', read_exact(host_socket, 4))
		ret = read_exact(host_socket, sz)
		if len(ret) == 1:
			print('Formatting packet failed')
		else:
			new_pkt = bson.BSON.decode(ret)
			print('got formatted pacekt')
			print(new_pkt)
			done_callback(new_pkt)


	io_loop = tornado.ioloop.IOLoop.instance()
	callback = functools.partial(read_from_sandbox, host)
	io_loop.add_handler(host.fileno(), callback, io_loop.READ)


	settings = [('code', str), ('code_url', str)]
	parameters = []

	description = '''Parse packets with python code'''

	formatter.start_formatting(l, description, settings, parameters, write_to_sandbox, True, init, io_loop)
