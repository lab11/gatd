Streamer Service
================

This service allows the incoming data to be sent to clients in a real time
streaming fashion. Many streamer modules can exist by creating a queue from
streamer exchange.


Creating a streamer module
--------------------------

Any streamer can receive all of the incoming packets by creating a queue and
binding it to the correct exchange. Example in python:

```python
result = self.amqp_chan.queue_declare(exclusive=True, auto_delete=True)
self.amqp_chan.queue_bind(exchange=STREAM_EXCHANGE, queue=result.method.queue, arguments=keys)
```

Note that the queue is set to auto delete. This is necessary because when the
streamer module quits the queue is no longer needed. Also, when binding the
queue to the exchange a `dict()` can be provided as the `arguments` argument.
This will cause rabbitmq to only put packets in the queue that have all of the
(key, value) pairs as specified by `keys`. This allows streamers to do a rough
filter of data to reduce the amount of extra packets they have to handle.


Available streamer modules
--------------------------

Clients that want real time streaming data can connect to one of the following
streamers.


### Socket.io with some history

This streamer is written in python and it supports
"streaming from the past". Basically instead of just streaming from when the
client connects and into the future, this server can stream data from a point
in the past. To do this, add the `time` key to the query with the value
as the number of milliseconds in the past to stream from.

This example will start 5 minutes in the past:

    sockio.emit('query', {'profile_id': MY_PROFILE,
	                      'time': 300000});

Usage:

    host: inductor.eecs.umich.edu:8082
    namespace: /stream



### Socket.io with history and no future

This streamer queries from the main collection so it has access
to all historical data, but no new data.

    sockio.emit('query', {'profile_id': MY_PROFILE,
	                      'time': 300000});

Usage:

    host: inductor.eecs.umich.edu:8083
    namespace: /stream


### Socket.io with history and replay

This streamer queries from the main collection and performs in 
"replay" mode. That is, it streams packets back as if they were coming
in in real time. So packets that originally came in five seconds apart will
be streamed to the client five seconds apart. In some cases real-time may
be too slow, so this streamer supports a speedup mode that scales the time
between streamed packets.

This streamer doesn't support the "time" key in the same way as the others.

    sockio.emit('query', {'profile_id': MY_PROFILE,
	                      'time': {'$gt': 300000}},
	                      '_speedup': 10.0);

Usage:

    host: inductor.eecs.umich.edu:8084
    namespace: /stream



Old Streamers
-------------

### Socket.io

This streamer uses socket.io to funnel data from the server to a browser. This
is the best approach if the client is a webpage.

    host: inductor.eecs.umich.edu:8080
    namespace: /stream


### TCP

For a more basic interface, a client can simply create a TCP connection
and receive packets over the connection.

    host: inductor.eecs.umich.edu
    port: 22500

Upon connecting, the client should send a JSON string representing the query
of the data it would like to receive. Currently the only supported query is
matching (key, value) pairs. So to receive all packets that measured the
temperature to be 70 degrees, send this JSON blob to the server:

    json.dumps({"temperature": 70})

For an example of usage, see the `receiver` folder.
