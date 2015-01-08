import pickle


import gatdBlock
import gatdLog

l = gatdLog.getLogger('dedup')

def cb (args, channel, method, prop, body):

	channel.basic_publish(exchange=args.exchange,
	                      body=pickle.dumps(body),
	                      routing_key=str(args.uuid))

	# Ack all packets
	channel.basic_ack(delivery_tag=method.delivery_tag)


settings = []
parameters = [('exchange', str)]

gatdBlock.start_block(l, 'Combine Queues', settings, parameters, cb)
