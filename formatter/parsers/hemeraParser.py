import IPy
import json
import struct
import parser

class hemeraParser (parser.parser) :

	source_addrs = ['2001:470:1f11:131a:8226:33eb:3455:36de']

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		if len(data) == 11:
			values = struct.unpack("!HHHHBH", data);
		elif len(data) == 9:
			values = struct.unpack("!HHHHB", data);

		ret['address']         = str(meta['addr'])
		ret['port']            = meta['port']
		ret['time'] 	       = meta['time']
		ret['temperature']     = values[1]
		ret['humidity']        = values[2]
		ret['light']           = values[3]
		ret['motion']          = bool(values[4])
		if len(values) == 6:
			ret['battery'] = values[5]
		ret['public']          = settings['public']

		print ret

		return ret


