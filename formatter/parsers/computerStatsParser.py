import IPy
import json
import struct
import parser

class computerStatsParser (parser.parser):

	name = 'Computer Stats'
	description = 'CPU, memory, disk, and network usage statistics for computers.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}


		datamap = json.loads(data[10:])


		ret['address']         = meta['addr']
		ret['port']            = meta['port']
		try:
			ret['time']        = datamap['time']
		except KeyError:
			ret['time']        = meta['time']
		ret['hostname']        = datamap['name']
		ret['cpu_usage']       = datamap['cpu']
		ret['memory_usage']    = datamap['memory']
		ret['disk_usage']      = datamap['disk']
		if 'net-sent' in datamap:
			ret['network_sent']    = datamap['net-sent']
		if 'net-recv' in datamap:
			ret['network_receive'] = datamap['net-recv']
		ret['public']          = settings['public']

		print str(IPy.IP(meta['addr'])) + ' usage: ' + str(datamap['cpu'])

		return ret