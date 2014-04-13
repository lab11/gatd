import IPy
import json
import struct
import parser
import semantic_version as semver
import urlparse

class gridwatchParser (parser.parser):

	name = 'GridWatch'
	description = 'Data from phones monitoring the power grid.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Parse the JSON blob
		post = json.loads(data[10:])
		
		headers = post['headers']

		if not 'content-type' in headers:
			return None

		if headers['content-type'] == 'application/x-www-form-urlencoded':

			vals = urlparse.parse_qs(post['data'])

			# Determine if this is dumbwatch or gridwatch
			if 'id' not in vals:
				# This is dumbwatch
				ret['phone_id'] = int(vals['u'][0])
				ret['phone_type'] = 'galaxy_s_dumbwatch'
				connection = vals['c'][0]
				if connection == 'w':
					ret['network'] = 'wifi'
				elif connection == 'm':
					ret['network'] = 'mobile'
				elif connection == 'o':
					ret['network'] = 'other'
				elif connection == 'd':
					ret['network'] = 'disconnected'
				event = vals['e'][0]
				if event == 'u':
					ret['event_type'] = 'unplugged'
				elif event == 'p':
					ret['event_type'] = 'plugged'
				elif event == 'w':
					ret['event_type'] = 'watch_dog'
				ret['android_id_truncated'] = vals['h'][0]
				ret['time'] = int(vals['t'][0]) # Use the timestamp from the phone
				ret['v'] = vals['v'][0]

			else:
				# This is GridWatch
				# Get values that should be present across all devices and versions
				ret['phone_id']    = vals['id'][0]
				ret['phone_type']  = vals.get('phone_type', (u'unknown',))[0]
				ret['os']          = vals['os'][0]
				ret['os_version']  = vals.get('os_version', (u'unknown',))[0]
				ret['app_version'] = vals.get('app_version', (u'unknown',))[0]
				ret['network']     = vals.get('network', (u'unknown',))[0]

				if ret['app_version'] == u'unknown':
					app_ver = semver.Version('0.0.0')
				else:
					app_ver = semver.Version(ret['app_version'], partial=True)

				# Handle the events and movement items
				if ret['os'] == u'android' and app_ver == semver.Version('0.0.0'):
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
					ret['event_type'] = vals['event_type'][0]
					if 'moved' in vals:
						ret['moved'] = vals['moved'][0].lower() == 'true'

				# Handle changes in location
				if ret['os'] == u'android' and app_ver < semver.Version('0.2.3'):
					ret['latitude']  = float(vals['latitude'][0])
					ret['longitude'] = float(vals['longitude'][0])
					ret['accuracy']  = -1.0
					ret['altitude']  = 0.0
					ret['loc_time']  = 0
					ret['speed']     = 0.0
				elif ret['os'] == 'android' and app_ver == semver.Version('0.2.3'):
					ret['altitude'] = 0.0
					ret['loc_time'] = 0
					ret['speed']    = 0.0
					if 'gps_latitude' in vals:
						ret['gps_latitude']  = float(vals['gps_latitude'][0])
						ret['gps_longitude'] = float(vals['gps_longitude'][0])
						ret['gps_accuracy']  = float(vals['gps_accuracy'][0])
					if 'network_latitude' in vals:
						ret['network_latitude']  = float(vals['network_latitude'][0])
						ret['network_longitude'] = float(vals['network_longitude'][0])
						ret['network_accuracy']  = float(vals['network_accuracy'][0])

					if 'gps_latitude' in ret and 'network_latitude' in ret:
						if ret['gps_accuracy'] < ret['network_accuracy']:
							ret['latitude']  = ret['gps_latitude']
							ret['longitude'] = ret['gps_longitude']
							ret['accuracy']  = ret['gps_accuracy']
						else:
							ret['latitude']  = ret['network_latitude']
							ret['longitude'] = ret['network_longitude']
							ret['accuracy']  = ret['network_accuracy']
					elif 'gps_latitude' in ret:
						ret['latitude']  = ret['gps_latitude']
						ret['longitude'] = ret['gps_longitude']
						ret['accuracy']  = ret['gps_accuracy']
					elif 'network_latitude' in ret:
						ret['latitude']  = ret['network_latitude']
						ret['longitude'] = ret['network_longitude']
						ret['accuracy']  = ret['network_accuracy']
					else:
						ret['latitude']  = -1.0
						ret['longitude'] = -1.0
						ret['accuracy']  = -1.0
				else:
					if 'gps_latitude' in vals:
						ret['gps_latitude']  = float(vals['gps_latitude'][0])
						ret['gps_longitude'] = float(vals['gps_longitude'][0])
						ret['gps_accuracy']  = float(vals['gps_accuracy'][0])
						ret['gps_altitude']  = float(vals['gps_altitude'][0])
						ret['gps_time']      = vals['gps_time'][0]
						ret['gps_speed']     = float(vals['gps_speed'][0])
					if 'network_latitude' in vals:
						ret['network_latitude']  = float(vals['network_latitude'][0])
						ret['network_longitude'] = float(vals['network_longitude'][0])
						ret['network_accuracy']  = float(vals['network_accuracy'][0])
						ret['network_altitude']  = float(vals['network_altitude'][0])
						ret['network_time']      = vals['network_time'][0]
						ret['network_speed']     = float(vals['network_speed'][0])

					if 'gps_latitude' in ret and 'network_latitude' in ret:
						if ret['gps_accuracy'] < ret['network_accuracy']:
							ret['latitude']  = ret['gps_latitude']
							ret['longitude'] = ret['gps_longitude']
							ret['accuracy']  = ret['gps_accuracy']
							ret['altitude']  = ret['gps_altitude']
							ret['loc_time']  = ret['gps_time']
							ret['speed']     = ret['gps_speed']
						else:
							ret['latitude']  = ret['network_latitude']
							ret['longitude'] = ret['network_longitude']
							ret['accuracy']  = ret['network_accuracy']
							ret['altitude']  = ret['network_altitude']
							ret['loc_time']  = ret['network_time']
							ret['speed']     = ret['network_speed']
					elif 'gps_latitude' in ret:
						ret['latitude']  = ret['gps_latitude']
						ret['longitude'] = ret['gps_longitude']
						ret['accuracy']  = ret['gps_accuracy']
						ret['altitude']  = ret['gps_altitude']
						ret['loc_time']  = ret['gps_time']
						ret['speed']     = ret['gps_speed']
					elif 'network_latitude' in ret:
						ret['latitude']  = ret['network_latitude']
						ret['longitude'] = ret['network_longitude']
						ret['accuracy']  = ret['network_accuracy']
						ret['altitude']  = ret['network_altitude']
						ret['loc_time']  = ret['network_time']
						ret['speed']     = ret['network_speed']
					else:
						ret['latitude']  = -1.0
						ret['longitude'] = -1.0
						ret['accuracy']  = -1.0
						ret['altitude']  = 0.0
						ret['loc_time']  = 0
						ret['speed']     = 0.0


				# Determine if this might correspond to a power outage
				if ret['event_type'] == 'unplugged':
					if 'moved' in ret:
						if ret['moved']:
							ret['power_on'] = True
						else:
							ret['power_on'] = False
				ret['time']       = int(vals['time'][0]) # Use the timestamp from the phone

		elif headers['content-type'] == 'application/octet-stream':
			ret['event_type'] = 'audio_post'
			ret['data'] = post['data']
			ret['time'] = meta['time']
			print(ret['data'])

		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['public']     = settings['public']

		return ret
