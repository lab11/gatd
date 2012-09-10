import dataParserBase
import struct

class dataParserHemeraSampler (dataParserBase.dataParserBase):

	# Returns a dict of formatted data
	def parse (self, data):
		ret = {}
		if len(data["data"]) == 9:
			unpack = struct.unpack(">HHHH?", data["data"])
		elif len(data['data']) == 11:
			unpack = struct.unpack(">HHHH?H", data['data'])

		ret["seq"] = unpack[0]
		ret["temperature_fahrenheit"] = -39.3 + 0.018*float(unpack[1])
		humidity_raw = float(unpack[2])
		ret["humidity"] = -2.0468 + (0.0367*humidity_raw) + (-0.0000015955*humidity_raw*humidity_raw)
		ret["light_lux"] = unpack[3]
		ret["motion"] = unpack[4]
	
		if len(data['data']) == 11:
			ret['battery_volts'] = (float(unpack[5]) / 4095.0)  * 3.44

		ret["address"] = data["address"]
		ret["timestamp"] = data["timestamp"]
		
		return ret;
		
	
	# Returns a list of the addresses this parser acts on
	def getAddresses (self):
		return ["2607:f018:8000:bbba:12:6d45:507f:a245", \
				"2607:f018:8000:bbba:12:6d45:507f:9e98", 
				"2607:f018:8000:bbba:12:6d45:507f:73e0", 
				"2607:f018:8000:bbba:12:6d45:507e:eacd", 
				"2607:f018:8000:bbba:12:6d45:507f:8f01", 
				"2607:f018:8000:bbba:12:6d45:507f:a115", 
				"2607:f018:8000:bbba:12:6d45:507f:9e5e", 
				"2607:f018:8000:bbba:12:6d45:507f:86ea", 
				"2607:f018:8000:bbba:12:6d45:507f:a012", 
				"2607:f018:8000:bbba:12:6d45:507f:dca3", 
				"2607:f018:8000:bbba:12:6d45:507f:8dee", 
				"2607:f018:8000:bbba:12:6d45:507f:824e", 
				"2607:f018:8000:bbba:12:6d45:50e7:235a", 
				"2607:f018:8000:bbba:12:6d45:507f:9bac", 
				"2607:f018:8000:bbba:12:6d45:507f:81ef", 
				"2607:f018:8000:bbba:12:6d45:507f:82ff", 
				"2607:f018:8000:bbba:12:6d45:507f:a1c3", 
				"2607:f018:8000:bbba:12:6d45:507f:abb1", 
				"2607:f018:8000:bbba:12:6d45:507f:aa9e"] 
	
