import IPy
import json
import struct
import parser

class doorrfidParser (parser.parser):

	name = 'Door Events'
	description = 'Door open, close, and access events.'

	source_addrs = ['2001:470:1f11:131a:2ab7:10c9:6e8b:f7a1',
                    '2001:470:1f11:131a:a6bc:f6e5:2144:1196',
                    '2001:470:1f11:131a:de6d:a438:fb41:788e',
					'2001:470:1f11:131a:c298:e552:5048:d86e']

	RFID_CARD_OPEN = 1
	RFID_CARD_FAIL = 2
	RFID_REMOTE_OPEN = 3
	RFID_REMOTE_FAIL = 4
	DOOR_OPEN = 5
	DOOR_CLOSE = 6

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		if len(data) == 0:
			return None

		pkt_type = struct.unpack('!B', data[0])[0]
		data = data[1:]

		if pkt_type == self.RFID_CARD_OPEN:	
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

		elif pkt_type == self.RFID_CARD_FAIL:
			# This RFID card does not have access to the room
			values = struct.unpack("!HLB", data)

			seq_no = values[0]
			rfid_code = int("0x{:x}{:x}".format(values[1], values[2]), 16)

			ret['type'] = "rfid_invalid"
			ret['seq_no'] = seq_no
			ret['rfid_code'] = rfid_code

		elif pkt_type == self.RFID_REMOTE_OPEN:
			# This was a remote udp packet that opened the door
			values = struct.unpack("!H2Q", data)
			remote_src_addr = int("0x{:0>16x}{:0>16x}".format(values[1], values[2]), 16)
			seq_no = values[0]

			ret['type'] = "udp"
			ret['opener_address'] = str(remote_src_addr)
			ret['seq_no'] = seq_no

		elif pkt_type == self.RFID_REMOTE_FAIL:
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

		elif pkt_type == self.DOOR_OPEN:
			# The door was opened
			print('door Opened')
			
			values = struct.unpack('!H', data)
			ret['seq_no'] = values[0]
			ret['type'] = 'door_open'


		elif pkt_type == self.DOOR_CLOSE:
			# The door was opened
			print('door Closed')
			
			values = struct.unpack('!H', data)
			ret['seq_no'] = values[0]
			ret['type'] = 'door_close'

		else:
			print('Unknown door packet.')
			return None


		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
