import binascii
import IPy
import json
import struct
import parser
import xml.etree.ElementTree as ET

class tedParser (parser.parser):

	# Parameters for this profile
	name = 'The Energy Detective'
	description = 'Whole-house energy metering.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		try:
			xml = ET.fromstring(data[10:])

			meter = xml.find('MTUVal')
			if meter is not None:
				# Commercial TED
				meter = meter.find('MTU1')

				ret['watts']   = float(meter.find('Value').text)
				ret['kva']     = float(meter.find('KVA').text)/1000.0
				ret['pf']      = float(meter.find('PF').text)/1000.0
				ret['voltage'] = float(meter.find('Voltage').text)/10.0

				current = meter.find('PhaseCurrent')
				ret['current_black'] = float(current.find('A').text)/10.0
				ret['current_red']   = float(current.find('B').text)/10.0
				ret['current_blue']  = float(current.find('C').text)/10.0

				voltage = meter.find('PhaseVoltage')
				ret['voltage_black'] = float(voltage.find('A').text)/10.0
				ret['voltage_red']   = float(voltage.find('B').text)/10.0
				ret['voltage_blue']  = float(voltage.find('C').text)/10.0
				raise UserWarning() # exit from processing the xml

			meter = xml.find('Voltage')
			if meter is not None:
				# Home TED
				voltage = meter.find('Total').find('VoltageNow')
				ret['voltage'] = float(voltage.text)/10.0

				power = xml.find('Power').find('Total').find('PowerNow')
				ret['watts'] = int(power.text)
				raise UserWarning()

		except UserWarning:
			pass
		except Exception as e:
			return None

		ret['gateway_id'] = meta['unique_id']
		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['time']       = meta['time']
		ret['public']     = settings['public']

		return ret
