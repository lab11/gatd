
import copy
import pickle

import arrow

import gatdBlock

def start_formatting(l, description, settings, parameters, callback):

	# This function handles getting packets from scope 'a' (the receive scope)
	# into a structure that can be formatted before eventually calling the
	# formatter.
	def formatter_callback (args, channel, method, prop, body):
		try:
			# Prepare the metadata for the formatter
			meta = {}

			meta['time_utc_iso'] = body['time_utc_iso']
			meta['input_src']    = body['src']

			if 'src_addr' in body:
				meta['src_addr'] = body['src_addr']
			if 'src_port' in body:
				meta['src_port'] = body['src_port']
			if 'headers' in body:
				meta['headers'] = body['headers']
			if 'http_get_url' in body:
				meta['http_get_url'] = body['http_get_url']

			t = arrow.get(meta['time_utc_iso'])
			meta['time_utc_timestamp'] = int(t.datetime.timestamp()*1000000)

			# Call the formatter with the data and the meta information
			ret = callback(body['data'], copy.deepcopy(meta))
			if type(ret) == list:
				# Formatters may return a list of items
				for item in ret:
					if type(item) != dict:
						l.warn('Formatter did not return a dict.')
					else:
						item['_gatd'] = meta
						# for target in routing_keys:
						channel.basic_publish(exchange='xch_scope_b',
						                      body=pickle.dumps(item),
						                      routing_key=str(args.uuid))

			elif type(ret) == dict:
				ret['_gatd'] = meta
				# for target in routing_keys:
				channel.basic_publish(exchange='xch_scope_b',
				                      body=pickle.dumps(ret),
				                      routing_key=str(args.uuid))
			elif ret == None:
				l.info('Formatter decided to drop packet or did not return anything.')

			else:
				l.warn('Formatter return not understood.')

		except:
			l.exception('Error formatting packet.')

		# Ack all packets
		l.info('herhe???')
		channel.basic_ack(delivery_tag=method.delivery_tag)

	# Start the connection to rabbitmq
	gatdBlock.start_block(l, description, settings, parameters, formatter_callback)
