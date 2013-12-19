import IPy
import json
import struct
import parser

class gridwatchParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Parse the JSON blob
		vals = json.loads(data[10:])
		
		ret['phone_id']   = vals['id'][0]
		ret['event_type'] = vals['event_type'][0]
		ret['latitude']   = float(vals['latitude'][0])
		ret['longitude']  = float(vals['longitude'][0])
		ret['phone_type'] = vals['phone_type'][0]
		ret['os']         = vals['os'][0]
		ret['os_version'] = vals['os_version'][0]
		ret['network']    = vals['network'][0]

		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['time']       = int(vals['time'][0]) # Use the timestamp from the phone
		ret['public']     = settings['public']

		return ret
