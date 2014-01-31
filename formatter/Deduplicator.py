
#
# Returns true if the packet is unique, false if it is a duplicate
#
# Each packet is in a hash table with its timestamp. If another packet
# comes in with the same data and a very similar timestamp it is considered
# a duplicate.
# In any case the packet is added with its timestamp

class Deduplicator (object):
	def __init__ (self):

		# dict of packet -> timestamp
		self.packet_hashes = {}


	# Call this function on the incoming data message to check if it is
	# a duplicate or not
	def check (self, port, addr, data, time):

		duplicate = False

		key = '{}{}{}'.format(port, addr, data)

		# Retrieve the last time this data was seen, or 0 if this is the first
		# time
		previous_time = self.packet_hashes.setdefault(key, 0)

		if previous_time > 0:
			if abs(time - previous_time) < 2000:
				duplicate = True

		# Put this packet in the dict for the next go around
		self.packet_hashes[key] = time

		return duplicate


