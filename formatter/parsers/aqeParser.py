import json
import struct
import parser

class aqeParser (parser.parser):

	# Parameters for this profile
	name = 'Air Quality Egg Parser'
	description = 'Measurements from the Air Quality Egg sensors.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		http = json.loads(data[10:])
		ret = json.loads(http['data'])

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
