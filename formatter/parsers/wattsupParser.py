import IPy
import json
import struct
import parser
import urlparse

class wattsupParser (parser.parser):

	name = 'Watts Up?'
	description = 'Load level energy metering.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Parse the JSON blob
		post = json.loads(data[10:])

		vals = urlparse.parse_qs(post['data'])

		ret['wattsupid']    = int(vals['id'][0])
		ret['watts']        = float(vals['w'][0])/10.0
		ret['volts']        = float(vals['v'][0])/10.0
		ret['amps']         = float(vals['a'][0])/10.0
		ret['watt-hours']   = float(vals['wh'][0])/10.0
		ret['max watts']    = float(vals['wmx'][0])/10.0
		ret['max volts']    = float(vals['vmx'][0])/10.0
		ret['max amps']     = float(vals['amx'][0])/10.0
		ret['min watts']    = float(vals['wmi'][0])/10.0
		ret['min volts']    = float(vals['vmi'][0])/10.0
		ret['min amps']     = float(vals['ami'][0])/10.0
		ret['power factor'] = float(vals['pf'][0])
		ret['power cycle']  = float(vals['pcy'][0])
		ret['frequency']    = float(vals['frq'][0])/10.0
		ret['volt-amps']    = float(vals['va'][0])/10.0

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret
