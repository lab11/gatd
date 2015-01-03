import ctypes
import socket
import ipaddress

IP_PKTINFO = 8
IPV6_PKTINFO = 50
IPV6_RECVPKTINFO = 49
SOL_IPV6 = 41

uint32_t = ctypes.c_uint32
in_addr_t = uint32_t

class in_addr(ctypes.Structure):
	_fields_ = [('s_addr', in_addr_t)]

class in6_addr_U(ctypes.Union):
	_fields_ = [
		('__u6_addr8', ctypes.c_uint8 * 16),
		('__u6_addr16', ctypes.c_uint16 * 8),
		('__u6_addr32', ctypes.c_uint32 * 4),
	]

class in6_addr(ctypes.Structure):
	_fields_ = [
		('__in6_u', in6_addr_U),
	]

class in_pktinfo(ctypes.Structure):
	_fields_ = [
		('ipi_ifindex', ctypes.c_int),
		('ipi_spec_dst', in_addr),
		('ipi_addr', in_addr),
	]

class in6_pktinfo(ctypes.Structure):
	_fields_ = [
		('ipi6_addr', in6_addr),
		('ipi6_ifindex', ctypes.c_uint),
	]

class xsocket (socket.socket):
	def __init__ (self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
		socket.socket.__init__ (self, family, type, proto)
		self.preparefromto()

	def preparefromto (self):
		if self.family in (socket.AF_INET, socket.AF_INET6):
			self.setsockopt(socket.SOL_IP, IP_PKTINFO, 1)
		if self.family == socket.AF_INET6:
			self.setsockopt(SOL_IPV6, IPV6_RECVPKTINFO, 1)

	def recvfromto (self):
		_to = None
		data, ancdata, msg_flags, _from = self.recvmsg(4096, socket.CMSG_LEN(5120 * 5))
		for anc in ancdata:
			if anc[0] == socket.SOL_IP and anc[1] == IP_PKTINFO:
				addr = in_pktinfo.from_buffer_copy(anc[2])
				addr = ipaddress.IPv4Address(memoryview(addr.ipi_addr).tobytes())
				_to = (str(addr), self.getsockname()[1])
			elif anc[0] == SOL_IPV6 and anc[1] == IPV6_PKTINFO:
				addr = in6_pktinfo.from_buffer_copy(anc[2])
				addr = ipaddress.ip_address(memoryview(addr.ipi6_addr).tobytes())
				_to = (str(addr), self.getsockname()[1])
		return data,_from,_to

	def sendtofrom(self, data, _to, _from):
		ancdata = []
		if type(_from) == tuple:
			_from = _from[0]
		addr = ipaddress.ip_address(_from)
		if type(addr) == ipaddress.IPv4Address:
			_f = in_pktinfo()
			_f.ipi_spec_dst = in_addr.from_buffer_copy(addr.packed)
			ancdata = [(socket.SOL_IP, IP_PKTINFO, memoryview(_f).tobytes())]
		elif self.family == socket.AF_INET6 and type(addr) == ipaddress.IPv6Address:
			_f = in6_pktinfo()
			_f.ipi6_addr = in6_addr.from_buffer_copy(addr.packed)
			ancdata = [(SOL_IPV6, IPV6_PKTINFO, memoryview(_f).tobytes())]
		return self.sendmsg([_data], ancdata, 0, _to)
