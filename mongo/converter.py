import sys
import MongoInterface
import DataParsers
import dataParserSimplePacket
import dataParserHemeraSampler
import dataParserWattsUp
import dataParser4908Door

MONGO_HOST = "localhost"
MONGO_PORT = 18222



try:
	
	parsers = DataParsers.DataParsers()
	parsers.add(dataParserSimplePacket.dataParserSimplePacket())
	parsers.add(dataParserHemeraSampler.dataParserHemeraSampler())
	parsers.add(dataParserWattsUp.dataParserWattsUp())
	parsers.add(dataParser4908Door.dataParser4908Door())
	
	# Connect to the mongo database
	mi = MongoInterface.MongoInterface(MONGO_HOST, MONGO_PORT)
	
	nodes = parsers.getAssignments()
	

	while True:
		
		data = mi.next()
		
		try:
			if data['address'] in nodes:

				if mi.hasLocation(data['address']):
					# parse and add to formatted data table
					parsed = nodes[data["address"]].parse(data)
					if parsed != None:
						print parsed['address']
						parsed = mi.addLocation(parsed)
						mi.writeFormatted(parsed)
					else:
						mi.archive(data)
				else:
					mi.archive(data)
			
			else:
				mi.archive(data)
				
			# Now that it is saved, delete it from the raw table
			mi.deleteRaw(data)
		
	#		sys.exit()

		except Exception:
			print "Exception in parser"
			print data
			mi.archive(data)
			mi.deleteRaw(data)
#			sys.exit()
				


except KeyboardInterrupt as e_ki:
	print "exiting..."
	exit(1)
