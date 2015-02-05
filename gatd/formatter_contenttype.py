
"""
Parse packets based on the value of the Content-Type header.
"""

import json
import urllib.parse

import werkzeug

import gatdLog
import formatter

l = gatdLog.getLogger('formatter-ct2')

def format (data, meta):

	l.info('Formatting packet.')

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
				l.info('Content: {} Type: {}'.format(data, ct[0]))

				if ct[0] == 'application/json':
					if type(data) == bytes:
						data = data.decode('utf-8')

					# JSON can be a string (invalid), list (only valid if each
					# element is a dict), or a dict (the normal case)
					ret = json.loads(data, strict=False)

				elif ct[0] == 'text/plain':
					if type(data) == bytes:
						data = data.decode('utf-8')
					ret = {'body': data.decode('utf-8')}

				elif ct[0] == 'application/x-www-form-urlencoded':
					if type(data) == bytes:
						data = data.decode('utf-8')
					ret = urllib.parse.parse_qs(data, keep_blank_values=True)

				else:
					ret = None

				l.info(ret)
				return ret

			except:
				# On any exception dump the packet
				l.exception('Error interpretting data')

		else:
			l.warn('Could not find header "Content-Type".')

	else:
		l.warn('No headers in packet meta.')

	return None


settings = []
parameters = []

description = '''Format packets based on their content-type.'''

formatter.start_formatting(l, description, settings, parameters, format)
