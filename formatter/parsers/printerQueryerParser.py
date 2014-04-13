import IPy
import json
import struct

class printerQueryerParser ():

	name = 'Printer Status'
	description = 'What the printer is up to.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		datamap = json.loads(data[10:])


		ret['address']   = meta['addr']
		ret['port']      = meta['port']
		ret['type']      = datamap['type']

		if ret['type'] == 'Print Job':
			ret['time_gatd'] = meta['time']
			ret['time']      = datamap['start']
			ret['time_end']  = datamap['end']
			ret['type']      = datamap['type']
			ret['user']      = datamap['user']
			ret['file']      = datamap['file']
			ret['pages']     = datamap['pages']
			ret['sides']     = datamap['sides']
			ret['duplex']    = datamap['duplex']
			ret['color']     = datamap['color']

		elif ret['type'] == 'Printer Status':
			ret['time']        = meta['time']
			ret['status_type'] = datamap['status_type']
			ret['status_val']  = datamap['status_val']

		ret['public']    = settings['public']

		return ret

