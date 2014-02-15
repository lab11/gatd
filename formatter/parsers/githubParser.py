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

		# Parse the JSON blob
		post = json.loads(data[10:])
		
		headers = post['headers']
		
	#	ret = post['data']
	#	ret['github_event'] = headers['x-github-event']i

		ret={}	

		print(type(headers))
		print(type(vals))

		return None

		ret['address']    = str(meta['addr'])
		ret['port']       = meta['port']
		ret['public']     = settings['public']

		return ret
