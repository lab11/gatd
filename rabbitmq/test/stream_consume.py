import IPy
import pika
import struct


HOSTNAME='inductor.eecs.umich.edu'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
channel = connection.channel()

#channel.queue_declare(queue='hello')

#print ' [*] Waiting for messages. To exit press CTRL+C'

def callback(ch, method, properties, body):
	print body

result = channel.queue_declare(exclusive=True, auto_delete=True)
hdr = {"seq_no":struct.pack("B",0), "x-match":"all"}
channel.queue_bind(exchange='streamer_exchange', queue=result.method.queue, arguments=hdr)

channel.basic_consume(callback,
                      queue=result.method.queue,
                      no_ack=True)
channel.start_consuming()

