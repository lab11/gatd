
class monjolo_ground_truth ():

	idname = 'wattsup_ground_truth'

	query = {}

	MON_PROFILE = '7aiOPJapXF'
	WUP_PROFILE = 'YWUr2G8AZP'

	# Dict of ccid_mac -> wattsup data
	wattsup = {}

	def __init__ (self):
		pass

	# Called when each packet is received by this handler.
	def process (self, pkt):

		if pkt['profile_id'] == self.WUP_PROFILE:
			if 'ccid_mac' in pkt:
				self.wattsup[pkt['ccid_mac']] = pkt

		elif pkt['profile_id'] == self.MON_PROFILE:
			if (not '_processor_freq' in pkt) or \
			   (pkt['_processor_freq'] != 'last'):
				# Only operate on coilcube_freq packets
				return None

			if pkt['ccid_mac'] in self.wattsup:
				# If we have ground truth add it to the packet
				newest_data = self.wattsup[pkt['ccid_mac']]
				pkt['ground_truth_watts'] = newest_data['watts']
				pkt['ground_truth_power_factor'] = newest_data['power factor']
				return pkt
			else:
				# If we don't still push this packet through so there is a clean
				# interface to get monjolo packets from
				return pkt
