import IPy
import json
import struct
import parser
#import semantic_version as semver

class gridwatchParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Parse the JSON blob
		vals = json.loads(data[10:])

		# Get values that should be present across all devices and versions
		ret['phone_id']    = vals['id'][0]
		ret['latitude']    = float(vals['latitude'][0])
		ret['longitude']   = float(vals['longitude'][0])
		ret['phone_type']  = vals.get('phone_type', ('unknown'))[0]
		ret['os']          = vals['os'][0]
		ret['os_version']  = vals.get('os_version', ('unknown'))[0]
		ret['app_version'] = vals.get('app_version', ('unknown'))[0]
		ret['network']     = vals.get('network', ('unknown'))[0]

		if ret['os'] == 'android' and ret['os_version'] == 'unknown':
			# This older version of android used event types that were
			# more descriptive than they are now. Translate those to what we
			# use now.
			event = vals['event_type'][0]
			if event == 'unplugged_moved':
				ret['event_type'] = 'unplugged'
				ret['moved'] = True
			elif event == 'unplugged_still':
				ret['event_type'] = 'unplugged'
				ret['moved'] = False
			elif event == 'plugged':
				ret['event_type'] = 'plugged'

		else:
			# This is all newer versions but could be extended to separate out
			# specific versions/oses if things change
			ret['event_type'] = vals['event_type'][0]
			if 'moved' in vals:
				ret['moved'] = vals['moved'][0].lower() == 'true'

		# Determine if this might correspond to a power outage
		if ret['event_type'] == 'unplugged':
			if 'moved' in ret:
				if ret['moved']:
					ret['power_on'] = True
				else:
					ret['power_on'] = False

		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['time']       = int(vals['time'][0]) # Use the timestamp from the phone
		ret['public']     = settings['public']

		return ret
