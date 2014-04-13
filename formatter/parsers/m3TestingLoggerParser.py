import binascii
import IPy
import json
import struct
import parser

class m3TestingLoggerParser (parser.parser):

	# Parameters for this profile
	name = 'M3 Testers Logging'
	description = 'Status of the M3 project development and testing.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

