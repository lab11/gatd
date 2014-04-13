import IPy
import json
import struct
import parser
import binascii
import datetime
import pytz
import time

class opoParser (parser.parser):

	name = 'Opo'
	description = 'Human inter-contact measurement.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		def convert_bcd(raw_t):
			h = hex(raw_t)
			t = int(h.split('x')[1])
			return t
		ret = {}

		# Opo-Specific
		s = struct.unpack('!10s H I H H 5B I', data)
		gatd_profile_id   = s[0]
		ret['tx_id']      = s[1]
		ret['seq']        = s[2]
		ret['last_tx_id'] = s[3]
		ret['t_ul_rf']    = s[4]
		ret['full_time']  = list(s[5:10])
		ret['last_seq']   = s[10]
		ret['range']      = float(ret['t_ul_rf'])/32000.0 * 340.29 - .12


		for i in range(len(ret['full_time'])):
			"""
			Time Format, from 0-5: second, minute, hour date, month. Year is assumed 2014
			"""
			ret['full_time'][i] = convert_bcd(ret['full_time'][i])

		sec = ret['full_time'][0]
		minute = ret['full_time'][1]
		hr = ret['full_time'][2]
		d = ret['full_time'][3]
		month = ret['full_time'][4]

		m_date = datetime.datetime(2014, month, d, hr, minute, sec, tzinfo=pytz.timezone('US/Eastern'))
		ret['full_time'] = time.mktime(m_date.timetuple())

		# Standard GATD Footer
		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['time']    = meta['time']
		ret['public']  = settings['public']

		return ret

