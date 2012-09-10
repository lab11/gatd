
"""
Class that manages the forwarders for the listener.

In your listener do something this:

	forwarders = dataForwarders.dataForwarders()
	forwarders.add_forwarder(dataForwarderDisplay.dataForwarderDisplay())
	forwarders.add_forwarder(dataForwarderMySQL.dataForwarderMySQL())
	
	forwarders.send(<packet data>)
	
"""


class DataParsers (object):

	def __init__ (self):
		self.parsers = []

	def add (self, new_parser):
		self.parsers.append(new_parser)
		
	def getAssignments (self):
		ret = {}
		for parser in self.parsers:
			addresses = parser.getAddresses()
			for address in addresses:
				ret[address] = parser
		
		return ret
