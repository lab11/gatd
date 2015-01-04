

blocks = {
	'receiver_udp_ipv6': {
		'name': 'UDP Receiver (IPv6)',
		'help': '''
Listener for UDP packets sent to an IPv6 address. Each instantiation of the
IPv6 UDP receiver is assigned a unique IPv6 destination address that you should
send UDP packets to to be collected by GATD. The entire UDP payload will be
collected and included in the stream for later processing.''',
		'target_group': None,
		'source_group': 'a',
		'single_instance': True,
		'routing_key': 'parameters.dst_addr',
		'parameters': [
			{
				'name': 'Destination Address',
				'help': 'This is the IPv6 address you should send UDP packets \
to for this receiver.',
				'key':  'dst_addr'
			},
			{
				'name': 'Destination Port',
				'help': 'This is the port you should send the UDP packets to.',
				'key':  'port'
			}
		]
	},

	'receiver_udp_ipv4': {
		'name': 'UDP Receiver (IPv4)',
		'help': '''
Listener for UDP packets sent to an IPv4 address. If possible, you should use
the IPv6 UDP receiver for UDP packets. This is only here for devices on
IPv4-only networks. Because there are a limited number of IPv4 addresses, there
can't be a unique destination IPv4 address for each receiver. Therefore, to
differentiate packets you must prepend the data in your UDP packet
with the UUID of this receiver instantiation. The UUID should be encoded
as ASCII bytes at the very beginning of the packet.
''',
		'target_group': None,
		'source_group': 'a',
		'single_instance': True,
		'parameters': [
			{
				'name': 'Destination Address',
				'help': 'The IP address to send the packets to.',
				'key':  'dst_addr'
			},
			{
				'name': 'Port',
				'help': 'The port to send the packets to.',
				'key':  'port'
			},
			{
				'name': 'Stream UUID',
				'help': 'This string should be the first 36 bytes of the UDP \
packet.',
				'key':  'receiver_id'
			}
		]
	},

	'receiver_http_post': {
		'name': 'HTTP POST Receiver',
		'help': 'Listens for HTTP posts and captures the POST data.',
		'target_group': None,
		'source_group': 'a',
		'single_instance': True,
		'parameters': [
			{
				'name': 'POST URL',
				'help': 'The URL to post to to ensure data reaches this stream.',
				'key': 'post_url'
			},
			{
				'name': 'Secret',
				'help': 'In the HTTP post, include the header "??" with \
this value so GATD knows that the request came from you.',
				'key': 'secret'
			}
		]
	},

	'queryer_http_get': {
		'name': 'HTTP Queryer',
		'help': '''
This block issues periodic HTTP GET requests to the specified URL. This is
useful for retreiving data from a source that doesn't output a stream of
data. The queryer is configured by specifying a URL that will be retreived
and the number of seconds between each request.
''',
		'target_group': None,
		'source_group': 'a',
		'single_instance': False,
		'settings': [
			{
				'name': 'URL',
				'help': 'The URL to issue the GET request to.',
				'key': 'url'
			},
			{
				'name': 'Period',
				'help': 'How many seconds between each request.',
				'key': 'interval',
				'default': 2,
				'type': 'int'
			}
		]
	},

	'deduplicator': {
		'name': 'Deduplicator',
		'help': '''
This block can be used to remove duplicate packets in an incoming data
stream. The deduplicator simply compares the data payload of the incoming
packets and drops packets with identical payloads. The "time" parameter
specifies how far back in time to look for identical packets. Also, the
deduplicator can verfiy that the lower 64 bits of the IPv6 source address
are identical in addition to the payload before determining that the
packet is a duplicate.
''',
		'target_group': 'a',
		'source_group': 'a',
		'single_instance': False,
		'settings': [
			{
				'name': 'Time',
				'help': 'Time, in minutes, to keep packets around to check \
for duplicates.',
				'key':  'time',
				'type': 'int',
				'default': 5
			},
			{
				'name': 'Check Interface Identifier',
				'help': 'Only declare two packets identical if the lower 64 \
bits of the source IPv6 addresses are the same.',
				'key':  'compare_addresses',
				'type': 'bool',
				'default': False
			}
		]
	},

	'formatter_python': {
		'name': 'Formatter (Python)',
		'help': '''
Process raw packets using Python code. The code can be specified by copying
it to the box or by specifying a URL where the code can be downloaded.''',
		'target_group': 'a',
		'source_group': 'b',
		'single_instance': False,
		'settings': [
			{
				'name': 'Python Code',
				'help': 'The code for the formatter.',
				'key':  'code',
				'type': 'textarea'
			},
			{
				'name': 'Python Code URL',
				'help': 'URL that points to a python file to use for the formatter.',
				'key': 'code_url'
			}
		]
	},

	'formatter_json': {
		'name': 'Formatter (JSON)',
		'help': '''
Automatically parse incoming data as JSON. This block understands data from
any of the input blocks and will interpret the data as JSON and expand the data
into a full object.''',
		'target_group': 'a',
		'source_group': 'b',
		'single_instance': False,
	},

	'formatter_contenttype': {
		'name': 'Formatter (Content-Type)',
		'help': '''
Automatically parse incoming data based on the Content-Type header from HTTP headers.
This block will only work with data streams that came from an HTTP like source
and that included the "Content-Type" field in their response/POST headers.
''',
		'target_group': 'a',
		'source_group': 'b',
		'single_instance': False,
	},

	'database_mongodb': {
		'name': 'MongoDB',
		'help': 'Store packets in a MongoDB database.',
		'target_group': 'b',
		'source_group': 'c',
		'icon': 'database',
		'single_instance': False,
	},

	'database_timeseries': {
		'name': 'Time Series DB',
		'help': 'Store packets in a time series database.',
		'target_group': 'b',
		'source_group': None,
		'single_instance': False,
	},

	'processor_python': {
		'name': 'Processor (Python)',
		'help': 'Manipulate packets with a Python script.',
		'target_group': 'b',
		'source_group': 'b',
		'single_instance': False,
		'settings': [
			{
				'name': 'Python Code',
				'help': 'The code for the formatter.',
				'key':  'code'
			}
		]
	},

	'meta_info_simple': {
		'name': 'Meta Info (Simple)',
		'help': '''
This block adds data from a static list to incoming packets. For instance, if
the incoming data is from sensors, you may wish to add the sensor's location to
the data packet. This block would let you create a list of sensor IDs and
locations and will automatically add the correct location key:value pair to
the data packet. To use, you specify the key:value pair that may be in the
data packet and the key:value pair to add to the packet if it is.''',
		'target_group': 'b',
		'source_group': 'b',
		'single_instance': False,
	},

	'streamer_socketio': {
		'name': 'Streamer (socket.io)',
		'help': 'Stream packets using the Socket.IO protocol.',
		'target_group': 'b',
		'source_group': None,
		'single_instance': False,
		'parameters': [
			{
				'name': 'Stream URL',
				'help': 'The stream url to use when connecting to the \
socket.io server.',
				'key': 'url'
			}
		]
	},

	'viewer': {
		'name': 'Viewer',
		'help': 'Get a glimse into the most recent packets for this stream.',
		'target_group': 'b',
		'source_group': None,
		'single_instance': True,
		'parameters': [
			{
				'name': 'URL',
				'help': 'The URL to use for the viewer.',
				'key': 'url'
			}
		]
	},

	'queryer': {
		'name': 'Queryer',
		'help': 'Issue queries to the database to retrieve historical data.',
		'target_group': 'c',
		'source_group': None,
		'single_instance': True,
		'parameters': [
			{
				'name': 'URL',
				'help': 'The URL to use for the queryer.',
				'key': 'url'
			}
		]
	},

	'replayer': {
		'name': 'Replayer',
		'help': 'Stream old data packets as if they were new.',
		'target_group': 'c',
		'source_group': None,
		'single_instance': True,
		'parameters': [
			{
				'name': 'URL',
				'help': 'The URL to use for the replayer.',
				'key': 'url'
			}
		]
	}
}

# These are other processes that need to be running for GATD to work.
# They are not user added blocks per se, which is why they are here.
global_blocks = [
	'streamer_socketio_public'
]