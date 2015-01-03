
import json

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-json')

def format (data, meta):

	l.debug(data)

	try:
		if type(data) == bytes:
			data = data.decode('utf-8')
		ret = json.loads(data, strict=False)

		# JSON can be just a string or list. If so, force it into
		# a dict
		if type(ret) != dict:
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
