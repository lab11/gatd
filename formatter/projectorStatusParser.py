import json

class projectorStatusParser ():

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		datamap = json.loads(data[10:])

		ret['address'] = meta['addr']
		ret['port']    = meta['port']
		ret['time']    = datamap['time']
		ret['on']      = datamap['on']

		ret['public']  = settings['public']

		return ret

