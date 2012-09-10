import pika


class RabbitInterface ():

	def __init__ (self, host):
		self.rmq_conn    = pika.BlockingConnection( \
		                    pika.ConnectionParameters(host=host))
		self.rmq_channel = self.rmq_conn.channel()

	def consume (self, callback, queue, no_ack):
		self.rmq_channel.basic_consume(callback, queue, no_ack)
		self.rmq_channel.start_consuming()

	def ack (self, dt):
		self.rmq_channel.basic_ack(dt)

	def publish (self, exchange, body):
		self.rmq_channel.basic_publish(exchange=exchange, routing_key='', body=body)

	def __del__ (self):
		self.rmq_conn.close()

