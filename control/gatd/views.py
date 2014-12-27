from pyramid.view import view_config


blocks = {
	'receiver_udp_ipv6': {
		'name': 'UDP Receiver (IPv6)',
		'help': 'Receives UDP packets on port ????.',
		'target_group': None,
		'source_group': 'a',
		'parameters': [
			{
				'name': 'Destination Address',
				'help': 'This is the IPv6 address you should send UDP packets \
to for this receiver.',
				'key':  'dst_addr'
			}
		]
	},

	'receiver_udp_ipv4': {
		'name': 'UDP Receiver (IPv4)',
		'help': 'Receives UDP packets on port ????.',
		'target_group': None,
		'source_group': 'a',
		'parameters': [
			{
				'name': 'Stream Magic Number',
				'help': 'This string should be the first X bytes of the UDP \
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
		'parameters': [
			{
				'name': 'POST URL',
				'help': 'The URL to post to to ensure data reaches this stream.',
				'key': 'post_url'
			}
		]
	},

	'queryer_http_get': {
		'name': 'HTTP Queryer',
		'help': 'Issue HTTP GET requests to a specific url periodically.',
		'target_group': None,
		'source_group': 'a',
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
		'help': 'Filter duplicate packets.',
		'target_group': 'a',
		'source_group': 'a',
		'settings': [
			{
				'name': 'Time',
				'help': 'Time, in minutes, to keep packets around to check \
for duplicates.',
				'key':  'time',
				'type': 'int',
				'default': 5
			}
		]
	},

	'formatter_python': {
		'name': 'Formatter (Python)',
		'help': 'Process raw packets using Python code',
		'target_group': 'a',
		'source_group': 'b',
		'settings': [
			{
				'name': 'Python Code',
				'help': 'The code for the formatter.',
				'key':  'code'
			}
		]
	},

	'database_mongo': {
		'name': 'MongoDB',
		'help': 'Store packets in a MongoDB database.',
		'target_group': 'b',
		'source_group': 'c'
	},

	'database_timeseries': {
		'name': 'Time Series DB',
		'help': 'Store packets in a time series database.',
		'target_group': 'b',
		'source_group': None
	},

	'processor_python': {
		'name': 'Processor (Python)',
		'help': 'Manipulate packets with a Python script.',
		'target_group': 'b',
		'source_group': 'b',
		'settings': [
			{
				'name': 'Python Code',
				'help': 'The code for the formatter.',
				'key':  'code'
			}
		]
	},

	'streamer_socketio': {
		'name': 'Streamer (socket.io)',
		'help': 'Stream packets using the Socket.IO protocol.',
		'target_group': 'b',
		'source_group': None,
		'parameter': [
			{
				'name': 'Stream URL Name',
				'help': 'The stream name to use when connecting to the \
socket.io server.',
				'key': 'stream_id'
			}
		]
	},

	'viewer': {
		'name': 'Viewer',
		'help': 'Get a glimse into the most recent packets for this stream.',
		'target_group': 'b',
		'source_group': None,
		'parameter': [
			{
				'name': 'URL Name',
				'help': 'The name to use for the viewer URL.',
				'key': 'viewer_id'
			}
		]
	},

	'queryer': {
		'name': 'Queryer',
		'help': 'Issue queries to the database to retrieve historical data.',
		'target_group': 'c',
		'source_group': None,
		'parameter': [
			{
				'name': 'URL Name',
				'help': 'The name to use for the queryer URL.',
				'key': 'query_id'
			}
		]
	},

	'replayer': {
		'name': 'Replayer',
		'help': 'Stream old data packets as if they were new.',
		'target_group': 'c',
		'source_group': None,
		'parameter': [
			{
				'name': 'URL Name',
				'help': 'The name to use for the replayer URL.',
				'key': 'replay_id'
			}
		]
	}
}




@view_config(route_name='home', renderer='templates/home.jinja2')
def home (request):
	return {}

@view_config(route_name='editor', renderer='templates/editor.jinja2')
def editor (request):


	block_buttons = [('Data Input', ['receiver_udp_ipv6',
	                                 'receiver_udp_ipv4',
	                                 'receiver_http_post',
	                                 'queryer_http_get']),
					 ('Receiver Helpers', ['deduplicator']),
					 ('Formatters', ['formatter_python']),
					 ('Processors', ['processor_python']),
					 ('Storage', ['database_mongo']),
					 ('Viewers', ['streamer_socketio', 'viewer', 'queryer', 'replayer'])
					 ]

	return {'blocks': blocks,
			'block_buttons': block_buttons}

@view_config(route_name='editor_block', renderer='json')
def editor_block (request):
	block_name = request.matchdict['block']

	if block_name not in blocks:
		return {'status': 'error'}

	block = blocks[block_name]


	return {'name': block['name'],
			'options': {
				'source_group': block['source_group'],
				'target_group': block['target_group']
			},
			'status': 'success'}




