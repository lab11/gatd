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

		# Opo-Specific
		s = struct.unpack('!10s H I H H 5B I', data)
		gatd_profile_id   = s[0]
		ret['tx_id']      = s[1]
		ret['seq']        = s[2]
		ret['last_tx_id'] = s[3]
		ret['t_rf']       = s[4]
		ret['full_time']  = s[5:10]
		ret['last_seq']   = s[11]
		ret['range']      = (float(ret['t_ultrasonic']) - float(ret['t_rf']))/32000.0 * 340.29 - .12

		print(ret)

		# Standard GATD Footer
		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

