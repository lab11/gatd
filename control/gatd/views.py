
import base64
import copy
import ipaddress
import json
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
import circus.client
import pika

import gatd.login_keys
import gatd.blocks


sys.path.append(os.path.abspath('../gatd'))
import gatdConfig


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

# def init_rabbitmq_exchanges ():

# 	amqp_conn = pika.BlockingConnection(
# 					pika.ConnectionParameters(
# 						host=gatdConfig.rabbitmq.HOST,
# 						port=gatdConfig.rabbitmq.PORT,
# 						credentials=pika.PlainCredentials(
# 							gatdConfig.control.USERNAME,
# 							gatdConfig.control.PASSWORD)
# 				))
# 	amqp_chan = amqp_conn.channel();


# 	for block_name, block in gatd.blocks.blocks.items():
# 		# Create the output exchange if this block can output packets.
# 		# There is no harm in declaring an exchange that already exists
# 		if block['source_group']:
# 			thischannel.exchange_declare('xch_{}'.format(block_name),
# 										 exchange_type='direct',
# 										 durable=True)


# def init_single_instance_blocks ():
# 	# Start all of the single instance blocks
# 	running['global'] = {}

# 	for block_name, block in gatd.blocks.blocks.items():
# 		if block['single_instance']:
# 			cmd = {
# 				'cmd': 'python3 {}'.format(block_name),
# 				'numprocesses': 1
# 			}
# 			running['global'][block_name] = circus.get_arbiter([cmd])
# 			running['global'][block_name].start()

# Take a given block and distill all of the unique features from it.
# This is used to tell if the block changed from one upload to the next
# so we know if we should re-start the process.
# Because of how we setup the routing keys in the rabbitmq queues, we only care
# about inputs to this block. If the inputs change we need to read from more
# queues, but we always send to the same exchange with the same routing key
# (the UUID of the sending block) regardless of the number of output queues.
def create_block_snapshot (block, connections):
	snap = {}

	# Iterate through all connections this block is involved in
	snap['sources'] = set()
	for connection in connections:
		if connection['target_uuid'] == block['uuid']:
			snap['sources'].add(connection['source_uuid'])

	# Save all settings for this block
	snap['settings'] = {}
	for setting in gatd.blocks.blocks[block['type']].get('settings', []):
		snap['settings'][setting['key']] = block[setting['key']]

	return snap

# This function causes GATD to start executing the profile
def run_profile (profile):

	comparer = unittest.TestCase()

	print('Uploading profile "{}"'.format(profile['name']))

	if profile['uuid'] != '9e5026f5-bdd0-466a-be5b-0fea8f35f2bb':
		return

	processes = running.setdefault(profile['uuid'], {})

	# Need a pika connection for creating queues
	amqp_conn = pika.BlockingConnection(
					pika.ConnectionParameters(
						host=gatdConfig.rabbitmq.HOST,
						port=gatdConfig.rabbitmq.PORT,
						virtual_host=gatdConfig.rabbitmq.VHOST,
						credentials=pika.PlainCredentials(
							gatdConfig.blocks.RMQ_USERNAME,
							gatdConfig.blocks.RMQ_PASSWORD)
				))
	amqp_chan = amqp_conn.channel();

	# Get a circus connection too
	circus_client = circus.client.CircusClient(endpoint='tcp://127.0.0.1:5555')

	# Iterate through all blocks in this profile
	for block in profile['blocks']:

		changed = False

		# Get more info about this block
		block_prototype = gatd.blocks.blocks[block['type']]

		# Get the distilled version of the block
		snap = create_block_snapshot(block, profile['connections'])

		# Check to see if we have seen this block before
		if block['uuid'] in processes:
			print('Block {} ({}) already running'.format(block['type'], block['uuid']))
			bprocess = processes[block['uuid']]

			# Check if the block changed since last time
			try:
				comparer.assertEqual(snap, bprocess['snapshot'])
			except:
				changed = True
				print('Block {} ({}) has changed. Restart!'.format(block['type'], block['uuid']))
			else:
				print('Block {} ({}) is the same. Just let it ride.'.format(block['type'], block['uuid']))

		else:
			# This is a new block so we need to start it
			print('Block {} ({}) is new'.format(block['type'], block['uuid']))
			changed = True

			bprocess = processes.setdefault(block['uuid'], {})
			bprocess['snapshot'] = snap

		if changed:
			if bprocess.get('started', False):
				print('Stopping block')
				to_circus = {
					'command': 'rm',
					'properties': {
						'name': block['uuid']
					}
				}
				circus_client.call(to_circus)


			#                make these queues
			#
			#   | source_conn[0] | --|    |-------|
			#   | source_conn[1] | -----> | block |
			#   | source_conn[2] | --|    |-------|
			#
			for src_uuid in snap['sources']:

				queue_name = '{}_{}'.format(src_uuid, block['uuid'])
				exchange_name = 'xch_scope_{}'.format(block_prototype['target_group'])

				# If we specified a special routing key (as in the IPv6 UDP
				# receiver, which filters on dest address) then use that as
				# the routing key. Else, just use the uuid of the source block.
				if 'routing_key' in block_prototype:
					fields = block_prototype['routing_key'].split('.')

					# Need to get the value out of the source block
					for srcblk in profile['blocks']:
						if srcblk['uuid'] == src_uuid:
							routing_key = srcblk[fields[0]][fields[1]]
							break
					else:
						print('Could not find the source block. Something is wrong.')
				else:
					routing_key = src_uuid

				print('Creating queue ({}) from ({}) with key ({})'.format(queue_name, exchange_name, routing_key))

				# Make queues for all of the inputs to this block
				amqp_chan.queue_declare(queue=queue_name,
				                        durable=True)
				amqp_chan.queue_bind(queue=queue_name,
				                     exchange=exchange_name,
				                     routing_key=routing_key)

			# If this is a single instance block (meaning there is one
			# process that runs globally) then we don't need to restart it.
			if block_prototype['single_instance']:
				continue

			cmd = 'python3 {path}/{block_type}.py --uuid {block_uuid} --source_uuid {sources}'\
				.format(path=os.path.abspath('../gatd'),
				        block_type=block['type'],
				        block_uuid=block['uuid'],
				        sources=' '.join(snap['sources']))

			print('CMD: {}'.format(cmd))

			# Actually start the block
			to_circus = {
				'command': 'add',
				'properties': {
					'cmd': cmd,
					'name': block['uuid'],
					'start': True
				}
			}
			circus_client.call(to_circus)
			bprocess['started'] = True




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
					                 'formatter_contenttype',
					                 'formatter_json']),
					 ('Processors', ['processor_python', 'meta_info_simple']),
					 ('Storage', ['database_mongodb']),
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
		block = copy.deepcopy(gatd.blocks.blocks[block_values['type']])
		block.update(block_values)

		if 'settings' in block:
			for setting in block['settings']:
				setting['value'] = block.get(setting['key'], '')

		if 'parameters' in block:
			for param in block['parameters']:
				param['value'] = block.get(param['key'], '')

		block_html += pyramid.renderers.render('templates/block_popup.jinja2', {'block': block})

	return {'blocks': gatd.blocks.blocks,
			'block_buttons': block_buttons,
			'profile': profile,
			'profile_html': block_html,
			'connections': profile.get('connections', [])}


@view_config(route_name='editor_block', renderer='json')
def editor_block (request):
	block_name = request.matchdict['block']

	if block_name not in gatd.blocks.blocks:
		return {'status': 'error'}

	block = copy.deepcopy(gatd.blocks.blocks[block_name])
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



