import IPy
import json
import struct
import parser
import binascii
class opoParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}
		print(len(data))
		print(binascii.hexlify(data))
		# Opo-Specific
		s = struct.unpack('!10s H H 5B B H H H H H H', data)
		gatd_profile_id                  = s[0]
		ret['tx_id']                     = s[1]
		ret['seq']                       = s[2]
		ret['full_time']                 = s[3:8]
		ret['buffer_index']              = s[8]
		ret['last_tx_id']                = s[9]
		ret['t_rf']                      = s[10]
		ret['t_ultrasonic_wake']         = s[11]
		ret['t_ultrasonic_wake_falling'] = s[12]
		ret['t_ultrasonic']              = s[13]
		ret['t_ultrasonic_falling']      = s[14]
		ret['range']                     = (float(ret['t_ultrasonic']) / float(ret['t_rf']))/32000.0 * 340.29 - .12

		print(ret)

		# Standard GATD Footer
		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

