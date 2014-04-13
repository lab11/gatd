import json
import parser

class githubParser (parser.parser):

	name = 'GitHub Events'
	description = 'Events on GitHub repositories'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):

		# Parse the JSON blob
		post = json.loads(data[10:])
		
		ret = json.loads(post['data'])
		ret['github_event'] = post['headers']['x-github-event']

		ret['address'] = str(meta['addr'])
		ret['time']    = meta['time']
		ret['port']    = meta['port']
		ret['public']  = settings['public']

		return ret
