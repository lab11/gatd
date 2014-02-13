import binascii
import IPy
import json
import struct
import parser
import xml.etree.ElementTree as ET

class ted5000Parser (parser.parser):

	# Parameters for this profile
	name = 'The Energy Detective'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		try:
			xml = ET.fromstring(data[10:])

			voltage = xml.find('Voltage').find('Total').find('VoltageNow')
			ret['voltage'] = float(voltage.text)/10.0

			power = xml.find('Power').find('Total').find('PowerNow')
			ret['watts'] = int(power.text)

		except Exception as e:
			return None

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']
		
		return ret
