import time

#
# Returns true if the packet is unique, false if it is a duplicate
#
# Each packet is in a hash table with its timestamp. If another packet
# comes in with the same data and a very similar timestamp it is considered
# a duplicate.
# In any case the packet is added with its timestamp

TIME_DELAY = 2000

class Deduplicator (object):
	def __init__ (self):

		# dict of packet -> timestamp
		self.packet_hashes = {}

		# array of timestamps
		self.timestamps = []

		# dict of timestamp -> packet
		self.time_hashes = {}


	# Call this function on the incoming data message to check if it is
	# a duplicate or not
	def check (self, port, addr, data, time):

		duplicate = False

		key = '{}{}{}'.format(port, addr, data)

		# Retrieve the last time this data was seen, or 0 if this is the first
		# time
		previous_time = self.packet_hashes.setdefault(key, 0)

		if previous_time > 0:
			if abs(time - previous_time) < TIME_DELAY:
				duplicate = True

		# Put this packet in the dict for the next go around
		self.packet_hashes[key] = time

		# Save the timestamp and backwards lookup
		self.timestamps.append(time)
		self.time_hashes[time] = key

		# Get rid of old packets from the dicts to reduce memory usage
		now = int(time.time()*1000)
		while True:
			time_check = self.timestamps[0]
			if now - time_check > TIME_DELAY:
				# Deleting this timestamp
				self.timestamps.remove(0)

				# Get the packet that corresponds to that time
				pkt = self.time_hashes[time_check]

				# Get the timestamp that that packet came in at
				saved_time = self.packet_hashes[pkt]

				# Check that a newer duplicate packet didn't come in and
				# update the timestamp
				if saved_time == time_check:
					# Go ahead and delete the packet
					del self.packet_hashes[pkt]
					del self.time_hashes[time_check]

			else:
				break


		return duplicate
