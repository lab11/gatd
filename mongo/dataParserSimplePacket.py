import dataParserBase
import struct

class dataParserSimplePacket (dataParserBase.dataParserBase):

	# Returns a dict of formatted data
	def parse (self, data):
		ret = {}
		ret["seq"] = struct.unpack(">H", data["data"][0:2])[0]
		ret["address"] = data["address"]
		ret["timestamp"] = data["timestamp"]
		return ret;
		
	
	# Returns a list of the addresses this parser acts on
	def getAddresses (self):
		return [""]	
