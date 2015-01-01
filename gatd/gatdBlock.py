
import argparse
import uuid

#                ---------
#   source  ---> | this  |  --> target
#    uuid        | block |       uuid
#                ---------
*
def start_block (l, description, settings, parameters, callback):
	# Use global values so we can "return" things from this function,
	# even though this function doesn't ever return
	global ars, routing_keys

	parser = argparse.ArgumentParser(description=description)

	for setting in settings:
		parser.add_argument('--{}'.format(setting[0]),
		                    type=setting[1],
		                    nargs=1,
		                    required=True)

	for param in parameters:
		parser.add_argument('--{}'.format(param[0]),
		                    type=param[1],
		                    nargs=1,
		                    required=True)

	parser.add_argument('--uuid',
	                    type=uuid.UUID,
	                    nargs=1,
	                    required=True)
	parser.add_argument('--source_uuid',
	                    nargs='+',
	                    type=uuid.UUID)
	parser.add_argument('--target_uuid',
	                    nargs='+',
	                    type=uuid.UUID)

	args = parser.parse_args()

	l.info('Arguments')
	for setting in settings:
		l.info('  {}: {}'.format(setting[0], getattr(args, setting[0])))
	for param in parameters:
		l.info('  {}: {}'.format(param[0], getattr(args, param[0])))
	l.info('  uuid: {}'.format(args.uuid))
	l.info('  source-uuid: {}'.format(args.source_uuid))
	l.info('  target-uuid: {}'.format(args.target_uuid))

	# Pre-enumerate all of the routing keys that we send packets to
	routing_keys = []
	for target in args.target_uuid:
		routing_keys.append('{}_{}'.format(args.uuid, str(target)))

	# Setup the connection to RabbitMQ
	def pika_on_channel (amqp_chan):

		for src in args.source_uuid:
			queue_name = '{}_{}'.format(str(src), str(args.uuid))

			l.info('Receiving packets from queue {}'.format(queue_name))

			amqp_chan.basic_consume(callback,
			                        queue=queue_name,
			                        no_ack=False)

	def pika_on_connection (unused_connection):
		amqp_conn.channel(pika_on_channel)

	amqp_conn = pika.SelectConnection(
					pika.ConnectionParameters(
						host=gatdConfig.rabbitmq.HOST,
						port=gatdConfig.rabbitmq.PORT,
						credentials=pika.PlainCredentials(
							gatdConfig.blocks.RMQ_USERNAME,
							gatdConfig.blocks.RMQ_PASSWORD)),
					pika_on_connection
				)
	amqp_conn.ioloop.start()