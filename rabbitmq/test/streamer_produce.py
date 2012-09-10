import pika
import sys
import json
import time
from StringIO import StringIO

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

#channel.exchange_declare(exchange='logs',type='fanout')

data = dict()
data['value'] = 10
data['location'] = 'home'
data['timestamp'] = 180927

io = StringIO()
json.dump(data, io)

message = io.getvalue()




properties = pika.BasicProperties(timestamp=time.time(), app_id='test streamer source', user_id='guest', content_type='test/json')

channel.basic_publish(exchange='streamer_exchange',
                      routing_key='',
                      body=message, properties=properties)
print " [x] Sent %r" % (message,)
connection.close()
