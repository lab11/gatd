
import base64
import copy
import ipaddress
import os
import sys
import unittest
import uuid

from pyramid.view import view_config
import pyramid.renderers
import pyramid.httpexceptions
import pyramid.security

import arrow
import authomatic
import authomatic.adapters

import gatd.login_keys


sys.path.append(os.path.abspath('../gatd'))
import gatdConfig


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
		'single_instance': False
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
		'single_instance': False
	},

	'database_mongo': {
		'name': 'MongoDB',
		'help': 'Store packets in a MongoDB database.',
		'target_group': 'b',
		'source_group': 'c',
		'icon': 'database',
		'single_instance': False
	},

	'database_timeseries': {
		'name': 'Time Series DB',
		'help': 'Store packets in a time series database.',
		'target_group': 'b',
		'source_group': None,
		'single_instance': False
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
		'single_instance': False
	},

	'streamer_socketio': {
		'name': 'Streamer (socket.io)',
		'help': 'Stream packets using the Socket.IO protocol.',
		'target_group': 'b',
		'source_group': None,
		'single_instance': True,
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

def receiver_udp_ipv6_parameters (block):
	ip = ipaddress.ip_address(os.urandom(16))
	port = gatdConfig.receiver_udp_ipv6.PORT
	for p in block['parameters']:
		if p['key'] == 'dst_addr':
			p['value'] = str(ip)
		if p['key'] == 'port':
			p['value'] = port

def receiver_udp_ipv4_parameters (block):
	dst_addr = gatdConfig.gatd.IPV4
	port = gatdConfig.receiver_udp_ipv4.PORT
	for p in block['parameters']:
		if p['key'] == 'dst_addr':
			p['value'] = dst_addr
		if p['key'] == 'port':
			p['value'] = port
		if p['key'] == 'receiver_id':
			p['value'] = block['uuid']

def receiver_http_post_parameters (block):
	secret = base64.b64encode(os.urandom(24)).decode('ascii')
	for p in block['parameters']:
		if p['key'] == 'post_url':
			p['value'] = 'http://post.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])
		if p['key'] == 'secret':
			p['value'] = secret

def streamer_socketio_parameters (block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://socketio.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def viewer_parameters (block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://viewer.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def queryer_parameters (block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://query.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def replayer_parameters (block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://replay.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

block_parameters_fns = {
	'receiver_udp_ipv6': receiver_udp_ipv6_parameters,
	'receiver_udp_ipv4': receiver_udp_ipv4_parameters,
	'receiver_http_post': receiver_http_post_parameters,
	'streamer_socketio': streamer_socketio_parameters,
	'viewer': viewer_parameters,
	'queryer': queryer_parameters,
	'replayer': replayer_parameters,
}


################################################################################
### GATD Block Processes                                                     ###
################################################################################

running = {}

def init_rabbitmq_exchanges ():

	amqp_conn = pika.BlockingConnection(
					pika.ConnectionParameters(
						host=gatdConfig.rabbitmq.HOST,
						port=gatdConfig.rabbitmq.PORT,
						credentials=pika.PlainCredentials(
							gatdConfig.control.USERNAME,
							gatdConfig.control.PASSWORD)
				))
	amqp_chan = amqp_conn.channel();


	for block_name, block in blocks.items():
		# Create the output exchange if this block can output packets.
		# There is no harm in declaring an exchange that already exists
		if block['source_group']:
			thischannel.exchange_declare('xch_{}'.format(block_name),
										 exchange_type='direct',
										 durable=True)


def init_single_instance_blocks ():
	# Start all of the single instance blocks
	running['global'] = {}

	for block_name, block in blocks.items():
		if block['single_instance']:
			cmd = {
				'cmd': 'python3 {}'.format(block_name),
				'numprocesses': 1
			}
			running['global'][block_name] = circus.get_arbiter([cmd])
			running['global'][block_name].start()

# Take a given block and distill all of the unique features from it.
# This is used to tell if the block changed from one upload to the next
# so we know if we should re-start the process.
def create_block_snapshot (block, connections):
	snap = {}

	# Iterate through all connections this block is involved in
	snap['source_conns'] = set()
	snap['target_conns'] = set()
	for connection in connections:
		if connection['source_uuid'] == block['uuid']:
			snap['source_conns'].add(connection['target_uuid'])
		if connection['target_uuid'] == block['uuid']:
			snap['target_conns'].add(connection['source_uuid'])

	# Save all settings for this block
	snap['settings'] = {}
	for setting in blocks[block['type']].get('settings', []):
		snap['settings'][setting['key']] = block[setting['key']]

	return snap

# This function causes GATD to start executing the profile
def run_profile (profile):

	comparer = unittest.TestCase()

	print('Uploading profile "{}"'.format(profile['name']))

	processes = running.setdefault(profile['uuid'], {})

	for block in profile['blocks']:
		if block['uuid'] in processes:
			bprocess = processes[block['uuid']]
			print('Block {} ({}) already running'.format(block['type'], block['uuid']))

			snap = create_block_snapshot(block, profile['connections'])

			try:
				comparer.assertEqual(snap, bprocess['snapshot'])
			except:
				print('Block {} ({}) has changed. Restart!'.format(block['type'], block['uuid']))
				#bprocess['cmd'].stop()
				#bprocess['cmd'] = start_block(block, profile['connections'])
				bprocess['snapshot'] = snap
			else:
				print('Block {} ({}) is the same. Just let it ride.'.format(block['type'], block['uuid']))

		else:
			print('Block {} ({}) is new'.format(block['type'], block['uuid']))
			bprocess = processes.setdefault(block['uuid'], {})

			bprocess['snapshot'] = create_block_snapshot(block, profile['connections'])
			#bprocess['cmd'] = start_block(block, profile['connections'])




################################################################################
### Authentication View                                                      ###
################################################################################

@view_config(route_name='login')
def login (request):
	response = pyramid.response.Response()

	provider_name = request.matchdict.get('provider_name')

	# request.registry.settings['chezbetty.email'])
	amatic = authomatic.Authomatic(config=gatd.login_keys.CONFIG,
	                               secret='fdsakjlfd',
	                               debug=True)

	result = amatic.login(authomatic.adapters.WebObAdapter(request, response), provider_name)

	if (not result) or (result.error) or (not result.user):
		# Handle all of the error cases
		response.write(pyramid.renderers.render('templates/loggedin_fail.jinja2', {}))
		return response


	if provider_name == 'github':
		token = result.user.data['access_token']
	elif provider_name == 'twitter':
		token = result.user.data['oauth_token_secret']
	else:
		print(result.user.data)
		return response
	print(token)

	if not (result.user.name and result.user.id):
		# Need to issue an update request to get more information about the user
		result.user.update()

	# Check to see if we already know about this user
	user = request.db['conf_users'].find_one({'token': token})

	if not user:
		user = {}
		user['created_time_utc_iso'] = arrow.utcnow().isoformat()
		user['token'] = token

	user['name'] = result.user.name
	user['email'] = result.user.email

	# Save/update this user
	#  if new: add user
	#  if existing: update info in case it changed
	userid = request.db['conf_users'].save(user)

	# Tell Pyramids about this now logged in user
	headers = pyramid.security.remember(request, str(userid))

	# Need to send the cookies to the client so we know about this user
	response.headers.extend(headers)

	# Add the basic "logged in" page to the response
	response.write(pyramid.renderers.render('templates/loggedin.jinja2', {}))

	# Return response. We have to do this for the authomatic magic to work.
	# It is not ideal, but I think I will do an HTML redirect and move on with
	# my life.
	return response






@view_config(route_name='home',
             renderer='templates/home.jinja2')
def home (request):
	return {}


@view_config(route_name='profiles',
             renderer='templates/profiles.jinja2',
             permission='loggedin')
def profiles (request):
	profiles = request.db['conf_profiles'].find({'_userid':str(request.user['_id'])})
	return {'profiles': profiles,
	        'user': request.user}


@view_config(route_name='profile_new',
             permission='loggedin')
def profile_new (request):
	profile = {}
	profile['name']    = 'New Profile'
	profile['uuid']    = str(uuid.uuid4())
	profile['_userid'] = str(request.user['_id'])

	request.db['conf_profiles'].save(profile)

	return pyramid.httpexceptions.HTTPFound(location=request.route_url('editor', uuid=profile['uuid']))


@view_config(route_name='editor',
             renderer='templates/editor.jinja2',
             permission='loggedin')
def editor (request):


	block_buttons = [('Data Input', ['receiver_udp_ipv6',
									 'receiver_udp_ipv4',
									 'receiver_http_post',
									 'queryer_http_get']),
					 ('Receiver Helpers', ['deduplicator']),
					 ('Formatters', ['formatter_python',
					                 'formatter_contenttypem',
					                 'formatter_json']),
					 ('Processors', ['processor_python', 'meta_info_simple']),
					 ('Storage', ['database_mongo']),
					 ('Viewers', ['streamer_socketio', 'viewer', 'queryer', 'replayer'])
					]

	profile_uuid = request.matchdict.get('uuid')
	profile = request.db['conf_profiles'].find_one({'_userid': str(request.user['_id']),
	                                                'uuid': profile_uuid})

	if not profile:
		#request.session.flash('Could not find that profile.', 'error')
		return pyramid.httpexceptions.HTTPFound(location=request.route_url('profiles'))

	block_html = ''
	for block_values in profile.get('blocks', []):
		block = copy.deepcopy(blocks[block_values['type']])
		block.update(block_values)

		if 'settings' in block:
			for setting in block['settings']:
				setting['value'] = block.get(setting['key'], '')

		if 'parameters' in block:
			for param in block['parameters']:
				param['value'] = block.get(param['key'], '')

		block_html += pyramid.renderers.render('templates/block_popup.jinja2', {'block': block})

	return {'blocks': blocks,
			'block_buttons': block_buttons,
			'profile': profile,
			'profile_html': block_html,
			'connections': profile.get('connections', [])}


@view_config(route_name='editor_block', renderer='json')
def editor_block (request):
	block_name = request.matchdict['block']

	if block_name not in blocks:
		return {'status': 'error'}

	block = copy.deepcopy(blocks[block_name])
	block['type'] = block_name
	block['uuid'] = str(uuid.uuid4())
	block['top'] = 0
	block['left'] = 0

	if block_name in block_parameters_fns:
		block_parameters_fns[block_name](block)

	block_html = pyramid.renderers.render('templates/block_popup.jinja2', {'block': block})

	return {'block': block,
			'html': block_html,
			'status': 'success'}


@view_config(route_name='editor_save',
			 request_method='POST',
			 renderer='json',
			 permission='loggedin')
def editor_save(request):
	data = request.json_body

	# Do some validation on the editor blob
	if 'uuid' not in data:
		print('No UUID in profile')
	else:

		data['_userid'] = str(request.user['_id'])

		# Save the current profile in the history collection
		# so we have a save history
		request.db['conf_profiles_history'].insert(data)

		# Update (or add) the profile to the main profiles
		# collection. .save() will use update if _id is present.
		old = request.db['conf_profiles'].find_one({'uuid': data['uuid'],
		                                            '_userid': data['_userid']})
		if old:
			data['_id'] = old['_id']

		request.db['conf_profiles'].save(data)


@view_config(route_name='editor_saveupload',
			 request_method='POST',
			 renderer='json',
			 permission='loggedin')
def editor_saveupload(request):
	data = request.json_body

	# Do some validation on the editor blob
	if 'uuid' not in data:
		print('No UUID in profile')
	else:

		data['_userid'] = str(request.user['_id'])

		# Save the current profile in the history collection
		# so we have a save history
		request.db['conf_profiles_history'].insert(data)

		# Update (or add) the profile to the main profiles
		# collection. .save() will use update if _id is present.
		old = request.db['conf_profiles'].find_one({'uuid': data['uuid'],
		                                            '_userid': data['_userid']})
		if old:
			data['_id'] = old['_id']

		request.db['conf_profiles'].save(data)

		run_profile(data)



