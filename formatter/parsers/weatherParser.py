import IPy
import json
import struct

class weatherParser ():

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		datamap = json.loads(data[10:])

	#	ret = datamap;
	#	ret[]
	#	ret['address']      = meta['addr']
	#	ret['port']         = meta['port']
	#	ret['time']         = meta['time']
	#	ret['hostname']     = datamap['name']
	#	ret['cpu_usage']    = datamap['cpu']
	#	ret['memory_usage'] = datamap['memory']
	#	ret['disk_usage']   = datamap['disk']
	#	ret['public']       = settings['public']

	#	print str(IPy.IP(meta['addr'])) + ' usage: ' + str(datamap['cpu'])

		return datamap


