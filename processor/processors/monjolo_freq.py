
class monjolo_freq ():

	idname = 'freq'

	query = {'profile_id': '7aiOPJapXF', # get data in the monjolo profile
	         '_processor_count': 0,      # get the raw data
	         'x-match': 'all'}           # match all keys in the query

	# Dict to keep track of the last values of different coilcubes
	# ccid -> [timestamp, count, seq_no]
	monjolos = {}

	def __init__ (self):
		pass

	def byte_subtract (self, a, b):
		if (a >= b):
			return a-b
		else:
			return a + (256-b)

	# Called when each packet is received by this handler.
	def process (self, pkt):
		# Determine if the incoming packet matches the query from the client

		# Make sure the keys we need are in the packet
		if 'ccid' not in pkt or \
		   'ccid_mac' not in pkt or \
		   'counter' not in pkt or \
		   'seq_no' not in pkt:
			return

		# Calculate the frequency
		if pkt['ccid'] in self.monjolos:
			last_data  = self.monjolos[pkt['ccid']]
			count_diff = self.byte_subtract(pkt['counter'], last_data[1]);
			time_diff  = pkt['time'] - last_data[0]
			if time_diff == 0:
				return
			# Calculate the activations per second
			freq = float(count_diff) / (float(time_diff)/1000.0)
			freq = round(freq, 4)

			pkt['freq'] = freq

		else:
			self.monjolos[pkt['ccid']] = [0]*3
			print("first sighting of this cc: {}".format(pkt['ccid_mac']))

		self.monjolos[pkt['ccid']][0] = pkt['time']
		self.monjolos[pkt['ccid']][1] = pkt['counter']
		self.monjolos[pkt['ccid']][2] = pkt['seq_no']

		# Now remove the seq no and counter
		del pkt['counter']
		del pkt['seq_no']

		return pkt
