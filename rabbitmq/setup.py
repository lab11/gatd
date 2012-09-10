##
## Sets up the necessary exchanges and queues.
## Binds the exchanges properly.
##



import pika
import sys

HOST='inductor.eecs.umich.edu'

connection	= pika.BlockingConnection(pika.ConnectionParameters(host=HOST))
channel		= connection.channel()

# Create the receive queue
q = channel.queue_declare(queue='receive_queue', durable=True)
# Create the exchange
channel.exchange_declare(exchange='receive_exchange', type='fanout', durable=True)
# Bind the exchange to the queue
channel.queue_bind(exchange='receive_exchange', queue=q.method.queue)

# Create the streamer queue
qs = channel.queue_declare(queue='streamer_queue', durable=True)
# Create the exchange
channel.exchange_declare(exchange='streamer_exchange', type='fanout', durable=True)
# Bind the exchange to the queue
channel.queue_bind(exchange='streamer_exchange', queue=qs.method.queue)

connection.close()

