#
# Sum watts up? readings for each location and create a new data stream
#

class wattsup_aggregate ():

	idname = 'local_aggregate'

	query = {'profile_id': 'YWUr2G8AZP',
	         '_processor_count': 0,
	         'x-match': 'all'}

	# dict of location->{wattsupid->watts}
	wattsups = {}


	# Called when each packet is received by this handler.
	def process (self, pkt):

		# Make sure the keys we need are in the packet
		if 'location_str' not in pkt or \
		   'watts' not in pkt:
			return

		opkt = {}
		opkt['time']             = pkt['time']
		opkt['public']           = pkt['public']
		opkt['profile_id']       = pkt['profile_id']
		opkt['_processor_count'] = 0

		location_fields = pkt['location_str'].split('|')
		agg_location = '|'.join(location_fields[0:-1])
		opkt['location_str'] = agg_location
		opkt['description'] = 'Aggregate from Watts Up? at {}' \
			.format(', '.join(location_fields[0:-1]))

		location_watts = self.wattsups.setdefault(agg_location, {})
		location_watts[pkt['wattsupid']] = pkt['watts']

		total = 0.0
		for watt in location_watts.itervalues():
			total += watt
		opkt['watts'] = total

		print(opkt)

		return opkt
