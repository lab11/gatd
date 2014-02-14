#!/usr/bin/env python2


import glob
import json
import os
import sys



def run_processor (processor_func, processor_name, pkt_body):
	print(processor_name)
	print(pkt_body)

	try:
		pkt = processor_func(json.loads(pkt_body))
	except Exception:
		# Any exception the processor returns just ignore
		print('exc')
		return

	if pkt == None:
		# The processor did not return a packet either out of an error
		# or because it didnt' want to
		return

	if type(pkt) != dict:
		# Not a dict, that is incorrect
		return

	# Update the processor history of this packet
	# Scan through to find the previous processors and which one was marked
	# as last
	proc_last = ''
	for key in pkt.keys():
		if key[0:10] == 'processor_':
			# one of the special keys
			if pkt[key] == 'last':
				proc_last = key

	count = pkt['processor_count']

	# Convert the last processor to the second to last
	if proc_last != '':
		pkt[proc_last] = count - 1

	# Mark this as the last processor
	pkt['processor_' + processor_name] = 'last'
	pkt['processor_count'] = count + 1

	print(pkt)




# Setup all processors with an instance and a rabbit mq connection
processors = glob.glob('processors/*.py')
for processor_filename in processors:
	processor_name = os.path.splitext(processor_filename.split('/')[1])[0]

	if processor_name == '__init__':
		continue

	exec('import processors.{}'.format(processor_name))
	processor_mod = sys.modules['processors.{}'.format(processor_name)]
	processor_n = getattr(processor_mod, processor_name)
	# Create a processor instance to run on packets
	processor = processor_n()


	cb = lambda ch, method, prop, body: run_processor(processor.process,
	                                                  processor_name,
	                                                  body)

	cb(None, None, None, json.dumps({'type':'coilcube_raw', 'ccid':1,
		'processor_first':0, 'processor_second':'last', 'processor_count':2}))

	cb(None, None, None, json.dumps({'type':'coilcube_raw', 'ccid':1,
		'processor_count':0}))




