import binascii
import IPy
import json
import struct
import parser
import xml.etree.ElementTree as ET

class projectorStatusParser (parser.parser):

	# Parameters for this profile
	name = 'InFocus Projector'
	description = 'Projector change events and status.'

	status  = ['off', 'on', 'turning_off', 'turning_on']
	sources = ['', 'VGA', 'HDMI 1', 'HDMI 2', 'S-Video', 'Composite']

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		try:
			xml = ET.fromstring(data[10:])

			ret['status']     = self.status[int(xml.find('pjPowermd').text)]
			ret['source']     = self.sources[int(xml.find('pjsrc').text)]
			ret['bulb_hours'] = int(xml.find('pjLamphr').text)

		except Exception as e:
			return None

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
