import dataParserBase

class dataParserWattsUp (dataParserBase.dataParserBase):

	# Returns a dict of formatted data
	def parse (self, data):
		if len(data['data']) > 10:
			ret = {}
#			print data
#			fields = data['data'][0:len(data['data'])-1].split(',')
			fields = data['data'].strip().split(',')
			for item in fields:
#				print item
				keyval = item.split('=')
				if keyval[0] == 'W':
					ret['wattsup_watts'] = float(keyval[1])
				elif keyval[0] == 'V':
					ret['wattsup_volts'] = float(keyval[1])
				elif keyval[0] == 'A':
					ret['wattsup_amps'] = float(keyval[1])
				elif keyval[0] == 'PF':
					ret['wattsup_power_factor'] = float(keyval[1])
				elif keyval[0] == 'f':
					ret['wattsup_frequency'] = float(keyval[1])

			ret["address"] = data["address"]
			ret["timestamp"] = data["timestamp"]
			
			return ret;
		else:
			return None
	
	# Returns a list of the addresses this parser acts on
	def getAddresses (self):
		return ["::ffff:141.212.110.153"]
			   
			   
			   
			   
	
