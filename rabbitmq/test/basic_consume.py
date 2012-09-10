import pika

HOSTNAME='inductor.eecs.umich.edu'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
channel = connection.channel()

#channel.queue_declare(queue='hello')

#print ' [*] Waiting for messages. To exit press CTRL+C'

def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)

channel.basic_consume(callback,
                      queue='receive_queue',
                      no_ack=True)

channel.start_consuming()

