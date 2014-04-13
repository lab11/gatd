import time

class shedCommitParser ():

	name = 'Shed Commits'
	description = 'Shed commits with user and commit message.'

	def __init__ (self):
		pass

	def parse (self, data, meta, extra, settings):
		ret = {}

		print "parsing shed data"

		lines = data.split('\n')
		t     = time.strptime(lines[2][0:19], '%Y-%m-%d %H:%M:%S')
		ti    = int(time.mktime(t)*1000)
		ret['user']    = lines[1]
		ret['time']    = ti
		ret['message'] = lines[4]
		ret['public']  = settings['public']

		print ret

		return ret
