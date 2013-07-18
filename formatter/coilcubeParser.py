import IPy
import json
import struct
import parser

class coilcubeParser (parser.parser) :

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Get the type of coilcube packet
		values = struct.unpack("!10BB", data[0:11])
		cc_version = values[10]
		data = data[11:]

		if cc_version == 1:
			if len(data) != 2:
				# not sure what to do
				print "COILCUBE: Too short!"
				return None

			# Parse out the rest of the values
			values = struct.unpack("!BB", data)

			ret['type'] = 'coilcube_raw'
			# remove the prefix and toggle the bit
			ret['ccid'] = (meta['addr'] & 0xFFFFFFFFFFFFFFFF) ^ (0x0200000000000000)
			ret['ccid'] = (meta['addr'] & 0xFFFFFFFFFFFFFFFF)
			ret['version'] = 1
			ret['seq_no'] = values[1]
			ret['counter'] = values[0]


		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

