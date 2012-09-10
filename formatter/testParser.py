import IPy

class testParser () :

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):

		ret = {}

		ret['address'] = meta['address']
		ret['port']    = meta['port''']
		ret['time']    = meta['time']
		ret['data']    = data
		ret['public']  = settings['public']

		print str(IPy.IP(address)) + ' ' + str(data)

		return ret


