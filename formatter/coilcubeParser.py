import IPy
import json
import struct
import parser

class coilcubeParser (parser.parser) :

	DATA_TYPE_RAW = 1
	DATA_TYPE_CALCULATED = 2

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Get the type of coilcube packet
		values = struct.unpack("!10BB", data[0:11])
		cc_type = values[10]

		if cc_type == self.DATA_TYPE_RAW:
			if len(data) < 29:
				# not sure what to do
				print "COILCUBE: Too short!"
				return

			# Parse out the rest of the values
			values = struct.unpack("!QQBB", data[11:29])

			ret['type'] = 'coilcube_raw'
			ret['ccid'] = values[0]
			ret['time'] = values[1]/1000
			ret['seq_no'] = values[2]
			ret['counter'] = values[3]


		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
#		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

