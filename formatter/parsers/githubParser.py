import json
import parser

class githubParser (parser.parser):

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):


		# Parse the JSON blob
		post = json.loads(data[10:])
		ret={}
#		ret = json.loads(post['data'])
		ret['github_event'] = post['headers']['x-github-event']

		ret['address'] = str(meta['addr'])
		ret['port']    = meta['port']
		ret['public']  = settings['public']

		print(ret)

		return ret
