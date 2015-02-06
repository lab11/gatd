
"""
Parse all input packets as JSON.
"""

import json


import gatdLog
import formatter

l = gatdLog.getLogger('formatter-json')

def format (data, meta):

	try:
		if type(data) == bytes:
			data = data.decode('utf-8')
		ret = json.loads(data, strict=False)

		# JSON can be just a string or list. Otherwise, force it into
		# a dict
		if type(ret) == dict or type(ret) == list:
			return ret
		else:
			ret = {'data': ret}

		return ret

	except:
		# On any exception dump the packet
		l.warn('Packet was not valid JSON')
		return None


settings = []
parameters = []

description = '''Parse packets as JSON'''

formatter.start_formatting(l, description, settings, parameters, format)
