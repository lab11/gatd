import IPy
import pika
import struct


HOSTNAME='inductor.eecs.umich.edu'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOSTNAME))
channel = connection.channel()

#channel.queue_declare(queue='hello')

#print ' [*] Waiting for messages. To exit press CTRL+C'

def callback(ch, method, properties, body):
#	print hex(body[18:26])
	record = struct.unpack('>4IHQ4s', body)
	ip = IPy.IP('0x%x%x%x%x' % tuple(record[0:4]))
	addr = ip
	port = record[4]
	time = record[5]
	data = record[6]
	print 'addr: ' + str(addr) + ' port: ' + str(port) + ' time: ' + str(time) + ' data: ' + data

channel.basic_consume(callback,
                      queue='receive_queue',
                      no_ack=True)

channel.start_consuming()

