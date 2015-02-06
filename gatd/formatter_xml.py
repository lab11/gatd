
"""
Parse all input packets as XML using xmltodict.
"""

import json

import xmltodict

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-xml')

def format (data, meta):

	try:
		if type(data) == bytes:
			data = data.decode('utf-8')

		ret = xmltodict.parse(data)

		# Run this through JSON to get rid of OrderedDicts
		ret = json.loads(json.dumps(ret))

		return ret

	except:
		# On any exception dump the packet
		l.warn('Packet was not valid XML or could not be converted')
		return None


settings = []
parameters = []

description = '''Parse packets as XML'''

formatter.start_formatting(l, description, settings, parameters, format)
