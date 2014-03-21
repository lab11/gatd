import IPy
import json
import struct
import parser

class opoParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		#values = struct.unpack('!BHHHHBH', data[10:])

		print(data)

		return None

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']
		
		return ret

