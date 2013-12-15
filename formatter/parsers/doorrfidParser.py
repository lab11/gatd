import IPy
import json
import struct
import parser

class doorrfidParser (parser.parser) :

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}


		if len(data) == 18:
			# This was a remote udp packet that opened the door
			values = struct.unpack("!H2Q", data)
			remote_src_addr = int("0x{:0>16x}{:0>16x}".format(values[1], values[2]), 16)
			seq_no = values[0]

			ret['type'] = "udp"
			ret['opener_address'] = str(remote_src_addr)
			ret['seq_no'] = seq_no

		elif len(data) == 15:
			# This was a RFID card swipe
			values = struct.unpack("!H8sLB", data)

			seq_no = values[0]
			uniqname = values[1]
			# Convert the cstring to just a string.
			# This really just means get rid of the null bytes
			for i,c in zip(range(8), uniqname):
				if c == '\x00':
					uniqname = uniqname[0:i]
					break
			rfid_code = int("0x{:x}{:x}".format(values[2], values[3]), 16)

			ret['type'] = "rfid"
			ret['seq_no'] = seq_no
			ret['uniqname'] = uniqname
			ret['rfid_code'] = rfid_code

		elif len(data) == 7:
			# This RFID card does not have access to the room
			values = struct.unpack("!HLB", data)

			seq_no = values[0]
			rfid_code = int("0x{:x}{:x}".format(values[1], values[2]), 16)

			ret['type'] = "rfid_invalid"
			ret['seq_no'] = seq_no
			ret['rfid_code'] = rfid_code

		elif len(data) > 18:
			# This was a remove udp packet with an invalid password
			values = struct.unpack("!H2QB{}s".format(len(data)-19), data)

			seq_no = values[0]
			remote_src_addr = int("0x{:0>16x}{:0>16x}".format(values[1], values[2]), 16)
			pwdlen = values[3]
			password = values[4]

			ret['type'] = "udp_failed"
			ret['seq_no'] = seq_no
			ret['opener_address'] = str(remote_src_addr)
			ret['password'] = password


		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
