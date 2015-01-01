
import json
import urllib.parse

import setproctitle
import werkzeug
setproctitle.setproctitle('gatd:form:ct')

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-ct')

def format (data, meta):

	if 'headers' in meta:
		ct_header = None

		ct_header = meta['headers'].get('content-type', None)
		if not ct_header:
			ct_header = meta['headers'].get('Content-Type', None)

		if ct_header:
			ct = werkzeug.http.parse_options_header(ct_header)

			# Check if we understand that content-type and if so, parse data
			# as that type

			try:
				if ct[0] == 'application/json':
					ret = json.loads(data, strict=False)

					# JSON can be just a string or list. If so, force it into
					# a dict
					if type(ret) != dict:
						ret = {'data': ret}


				elif ct[0] == 'text/plain':
					ret = {'body': data}


				elif ct[0] == 'application/x-www-form-urlencoded'
					ret = urllib.parse.parse_qs(data, keep_blank_values=True)


				return ret

			except:
				# On any exception dump the packet
				return None

		else:
			l.warn('Could not find header "Content-Type".')

	else:
		l.warn('No headers in packet meta.')

	return None



settings = []
parameters = []

description = '''Format packets based on their content-type.'''


formatter.start_formatting(l, description, settings, parameters, format)
