

class dataParserBase (object):

	# Returns a dict of formatted data
	def parse (self, data):
		raise NotImplementedError("not implemented")
	
	# Returns a list of the addresses this parser acts on
	def getAddresses (self):
		raise NotImplementedError("not implemented")
		
