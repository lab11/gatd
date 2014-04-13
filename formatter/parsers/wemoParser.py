import binascii
import IPy
import json
import struct
import parser

class wemoParser (parser.parser):

	# Parameters for this profile
	name = 'WeMo Parser'
	description = 'Belkin WeMo data.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = json.loads(data[10:])

		ret['port']    = meta['port']
		ret['address'] = str(meta['addr'])
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
