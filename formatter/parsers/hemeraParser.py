import IPy
import json
import struct
import parser

class hemeraParser (parser.parser):

	name = 'Hemera Sensor Data'
	description = 'Room monitoring sensor data. Light, humidity, temperature, and motion.'

	source_addrs = ['2001:470:1f11:131a:8226:33eb:3455:36de']

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		if len(data) > 11:
			# This is from the new version of the application where the
			# profile_id is sent at the beginning of the packet
			if len(data) == 22:
				values = struct.unpack('!BHHHHBH', data[10:])
			elif len(data) == 20:
				values = struct.unpack('!BHHHHB', data[10:])
			else:
				return None

			ret['version'] = values[0]
			ret['seqno']   = values[1]
			ret['temperature'] = values[2]
			ret['humidity']    = values[3]
			ret['light']       = values[4]
			ret['motion']      = bool(values[5])
			if len(values) == 7:
				ret['battery'] = values[6]

		else:
			# This is the older app

			if len(data) == 11:
				values = struct.unpack("!HHHHBH", data);
			elif len(data) == 9:
				values = struct.unpack("!HHHHB", data);
			else:
				return None

			ret['temperature'] = values[1]
			ret['humidity']    = values[2]
			ret['light']       = values[3]
			ret['motion']      = bool(values[4])
			if len(values) == 6:
				ret['battery'] = values[5]


		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']
		
		return ret

