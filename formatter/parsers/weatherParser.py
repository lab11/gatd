import IPy
import json
import struct

class weatherParser ():

	name = 'Weather'
	description = 'Weather information.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		datamap = json.loads(data[10:])

		return datamap
