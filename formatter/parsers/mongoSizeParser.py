import binascii
import IPy
import json
import struct
import parser

class mongoSizeParser (parser.parser):

	# Parameters for this profile
	name = 'MongoDB Size Stats'
	description = 'Tracking the size of the MongoDB database for GATD.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = json.loads(data[10:])

		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
