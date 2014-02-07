import binascii
import IPy
import json
import struct
import parser
import xml.etree.ElementTree as ET

class tedParser (parser.parser):

	# Parameters for this profile
	name = 'The Energy Detective'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		try:
			xml = ET.fromstring(data[10:])

			meter = xml.find('MTUVal').find('MTU1')

			ret['value']   = meter.find('Value').text
			ret['kva']     = meter.find('KVA').text
			ret['pf']      = meter.find('PF').text
			ret['voltage'] = meter.find('Voltage').text
			ret['phase']   = meter.find('Phase').text


		except Exception as e:
			return None

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

