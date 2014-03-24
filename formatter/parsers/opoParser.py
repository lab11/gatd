import IPy
import json
import struct
import parser
import binascii

class opoParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		def convert_bcd(raw_t):
			h = hex(raw_t)
			t = int(h.split('x'))
			return t
		ret = {}

		# Opo-Specific
		s = struct.unpack('!10s H I H H 5B I', data)
		gatd_profile_id   = s[0]
		ret['tx_id']      = s[1]
		ret['seq']        = s[2]
		ret['last_tx_id'] = s[3]
		ret['t_ul_rf']    = s[4]
		ret['full_time']  = s[5:10]
		ret['last_seq']   = s[10]
		ret['range']      = float(ret['t_ul_rf'])/32000.0 * 340.29 - .12

		for i in range(len(ret['full_time'])):
			"""
			Time Format, from 0-5: second, minute, hour date, month. Year is assumed 2014
			"""
			ret['full_time'][i] = convert_bcd(ret['full_time'][i])

		print(ret)

		# Standard GATD Footer
		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

