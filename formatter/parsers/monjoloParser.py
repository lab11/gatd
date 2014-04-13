import binascii
import IPy
import json
import struct
import parser

class monjoloParser (parser.parser):

	# Parameters for this profile
	name = 'Monjolo'
	description = 'Energy-harvesting pulse meters.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Get the type of coilcube packet
		values = struct.unpack("!10BB", data[0:11])
		cc_version = values[10]
		data = data[11:]

		if cc_version >= 1 and cc_version <= 5:
			if len(data) != 2:
				# not sure what to do
				print "COILCUBE: Too short!"
				return None

			# Parse out the rest of the values
			values = struct.unpack("!BB", data)

			ret['type'] = 'coilcube_raw'
			# remove the prefix and toggle the bit
			ret['ccid'] = str(int((meta['addr'] & 0xFFFFFFFFFFFFFFFF) ^ (0x0200000000000000)))
			# Create a nicely formated ccid
			# ex: 00:11:22:33:44:55:66:77
			ccid = '{:0>16x}'.format(int(ret['ccid']))
			ret['ccid_mac'] = ':'.join([ccid[i:i+2] for i in range(0, 16, 2)])
			ret['version'] = cc_version
			ret['seq_no'] = values[1]
			ret['counter'] = values[0]
		else:
			print("cc version: {}".format(cc_version))
			return None

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

