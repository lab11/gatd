import IPy
import json
import struct
import parser
import semantic_version as semver
import urlparse

class githubParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		# Parse the JSON blob
		post = json.loads(data[10:])
		
		headers = post['headers']
		vals = post['data']

		print(headers)
		print(vals)

		return None

		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['public']     = settings['public']

		return ret
