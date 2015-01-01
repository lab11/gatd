
import json

import setproctitle
setproctitle.setproctitle('gatd:form:json')

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-json')

def format (data, meta):

	try:
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
