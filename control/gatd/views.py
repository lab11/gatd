
import base64
import copy
import ipaddress
import json
import os
import pprint
import shlex
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


def receiver_udp_ipv6_parameters (profile, block):
	ip = ipaddress.ip_address(os.urandom(16))
	port = gatdConfig.receiver_udp_ipv6.PORT
	for p in block['parameters']:
		if p['key'] == 'dst_addr':
			p['value'] = str(ip)
		if p['key'] == 'port':
			p['value'] = port

def receiver_udp_ipv4_parameters (profile, block):
	dst_addr = gatdConfig.gatd.IPV4
	port = gatdConfig.receiver_udp_ipv4.PORT
	for p in block['parameters']:
		if p['key'] == 'dst_addr':
			p['value'] = dst_addr
		if p['key'] == 'port':
			p['value'] = port
		if p['key'] == 'receiver_id':
			p['value'] = block['uuid']

def receiver_http_post_parameters (profile, block):
	secret = base64.b64encode(os.urandom(24)).decode('ascii')
	for p in block['parameters']:
		if p['key'] == 'post_url':
			p['value'] = 'http://post.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])
		if p['key'] == 'secret':
			p['value'] = secret

def meta_keyvalue_parameters (profile, block):
	for p in block['parameters']:
		if p['key'] == 'edit_url':
			p['value'] = '/editor/meta_keyvalue/{}/{}'\
			.format(profile['uuid'], block['uuid'])

def streamer_parameters (profile, block):
	for p in block['parameters']:
		if p['key'] == 'socketio_url':
			p['value'] = 'http://socketio.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])
		elif p['key'] == 'websocket_url':
			p['value'] = 'ws://websocket.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def viewer_parameters (profile, block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://viewer.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def queryer_parameters (profile, block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://query.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

def replayer_parameters (profile, block):
	for p in block['parameters']:
		if p['key'] == 'url':
			p['value'] = 'http://replay.{}/{}'\
			.format(gatdConfig.gatd.HOST, block['uuid'])

block_parameters_fns = {
	'receiver_udp_ipv6': receiver_udp_ipv6_parameters,
	'receiver_udp_ipv4': receiver_udp_ipv4_parameters,
	'receiver_http_post': receiver_http_post_parameters,
	'meta_keyvalue': meta_keyvalue_parameters,
	'streamer': streamer_parameters,
	'viewer': viewer_parameters,
	'queryer': queryer_parameters,
	'replayer': replayer_parameters,
}





################################################################################
### GATD Block Processes                                                     ###
################################################################################

def start_block (uuid, block, block_prototype, circus_client):
	cmd = 'python3 {path}/{block_type}.py --uuid {block_uuid} --source_uuid {sources}'\
		.format(path=os.path.abspath('../gatd'),
		        block_type=block_prototype.get('script', block['type']),
		        block_uuid=uuid,
		        sources=' '.join(block['source_uuids']))

	print('  cmd: {}'.format(cmd))

	cmd_args = []

	# Add settings
	for k,v in block['settings'].items():
		cmd_args.append('--{}'.format(k))
		cmd_args.append(shlex.quote(v))

	# Add arguments
	for k,v in block['parameters'].items():
		cmd_args.append('--{}'.format(k))
		cmd_args.append(shlex.quote(v))

	# Add "hidden" arguments. These are needed to run the block
	# but aren't shown to the user.
	for param in block_prototype.get('hidden_parameters', []):
		cmd_args.append('--{}'.format(param['key']))
		cmd_args.append(shlex.quote(param['value']))

	print('  args: {}'.format(cmd_args))

	to_circus = {
		'command': 'add',
		'properties': {
			'cmd': cmd,
			'args': cmd_args,
			'name': uuid,
			'start': True
		}
	}
	circus_client.call(to_circus)

def stop_block (uuid, circus_client):
	to_circus = {
		'command': 'rm',
		'properties': {
			'name': uuid,
			'waiting': True
		}
	}
	circus_client.call(to_circus)

def query_block_exists (uuid, circus_client):
	to_circus = {
		'command': 'status',
		'properties': {
			'name': uuid
		}
	}
	response = circus_client.call(to_circus)
	return response['status'] != 'error'


# Distills an entire profile down to just the essential pieces for running
# the profile. This is used to check if the profile has changed, and if
# so, what blocks need to be restarted.
def create_running_profile (profile):

	rp = {'uuid': profile['uuid'],
	      'blocks': {}}

	for block in profile['blocks']:
		newblock = rp['blocks'][block['uuid']] = {}

		newblock['type'] = block['type']

		# Add all connections that go into the current block
		newblock['source_uuids'] = []
		for connection in profile['connections']:
			if connection['target_uuid'] == block['uuid']:
				newblock['source_uuids'].append(connection['source_uuid'])

		# Keep track of all settings for the current block
		newblock['settings'] = {}
		for setting in gatd.blocks.blocks[block['type']].get('settings', []):
			newblock['settings'][setting['key']] = block[setting['key']]

		# Keep track of all parameters for the current block (for convenience)
		newblock['parameters'] = {}
		for param in gatd.blocks.blocks[block['type']].get('parameters', []):
			newblock['parameters'][param['key']] = block[param['key']]

	return rp


# This function causes GATD to start executing the profile
def run_profile (request, profile):
	print(profile)

	def create_queue (src, dst, block_prototype, profile, db):

		if block_prototype.get('virtual_queues', False):
			# If this block uses virtual queues that means that there is a line
			# drawn to it on the editor but that doesn't correspond to an
			# actual queue. For instance, the database blocks do not output
			# packets, but can connect to another block to signify a
			# relationship.
			# Virtual queues are stored in the database and the blocks
			# that use them query the database to find out what blocks they
			# are connected to.

			print('  Creating virtual queue from src {}'.format(src))

			query = {'uuid': dst}

			existing = db['conf_virtual_queues'].find_one(query)
			if not existing:
				db['conf_virtual_queues'].insert(query)

			push = {'$push': {
						'source_uuids': src
					}}
			db['conf_virtual_queues'].update(query, push, upsert=True)

			return


		queue_name = '{}_{}'.format(src, dst)
		exchange_name = 'xch_scope_{}'.format(block_prototype['target_group'])

		# If we specified a special routing key (as in the IPv6 UDP
		# receiver, which filters on dest address) then use that as
		# the routing key. Else, just use the uuid of the source block.
		if 'routing_key' in block_prototype:
			fields = block_prototype['routing_key'].split('.')

			# Need to get the value out of the source block
			for srcblk in profile['blocks']:
				if srcblk['uuid'] == src:
					routing_key = srcblk[fields[0]][fields[1]]
					break
			else:
				print('  Could not find the source block. Something is wrong.')
		else:
			routing_key = src

		print('  Creating queue ({}) from ({}) with key ({})'.format(queue_name, exchange_name, routing_key))

		# Make queues for all of the inputs to this block
		amqp_chan.queue_declare(queue=queue_name,
		                        durable=True)
		amqp_chan.queue_bind(queue=queue_name,
		                     exchange=exchange_name,
		                     routing_key=routing_key)

	def delete_queue (src, dst, block_prototype, profile, db):

		if block_prototype.get('virtual_queues', False):
			print('  Removing virtual queue from src {}'.format(src))

			query = {'uuid': dst}
			pull = {'$pull': {
						'source_uuids': src
					}}
			db['conf_virtual_queues'].update(query, pull, upsert=True)

			return

		queue_name = '{}_{}'.format(src, dst)
		print('  removing queue {}'.format(queue_name))
		amqp_chan.queue_delete(queue=queue_name)


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
	circus_client = circus.client.CircusClient(endpoint='tcp://{host}:{port}'\
		.format(host=gatdConfig.circus.HOST, port=gatdConfig.circus.PORT))

	# Use this to compare settings if need be
	comparer = unittest.TestCase()
	pp = pprint.PrettyPrinter()


	print('####')
	print('#### Uploading profile "{}"'.format(profile['name']))
	print('####')


	# Start by getting the stored copy of what is currently executing
	existing = request.db['conf_profiles_running'].find_one({'uuid':profile['uuid']})

	print('existing')
	pp.pprint(existing)

	# Get a "running profile" for the profile we just saved
	newprofi = create_running_profile(profile)

	print('newprofi')
	pp.pprint(newprofi)

	# Start by removing old blocks
	if existing:
		for block_uuid,content in existing['blocks'].items():
			if block_uuid not in newprofi['blocks']:

				print('Block {} ({}) is no longer present'.format(content['type'], block_uuid))

				# Check to see if this is a single instance (global) block
				# or it runs on a per-profile based. If it's per-profile,
				# stop the process
				block_prototype = gatd.blocks.blocks[content['type']]
				if block_prototype['single_instance'] == False:
					print('  stopping block.')
					stop_block(block_uuid, circus_client)

				# Delete all queues that went to this block
				for src in content['source_uuids']:
					delete_queue(src, block_uuid, block_prototype, profile, request.db)


	# Iterate through the new blocks, detecting changes
	for block_uuid,content in newprofi['blocks'].items():
		print('Processing block {} ({})'.format(content['type'], block_uuid))


		changed = False
		block_prototype = gatd.blocks.blocks[content['type']]

		if (not existing) or (block_uuid not in existing['blocks']):
			print('  new')

			# Create queues for this block
			for src in content['source_uuids']:
				create_queue(src, block_uuid, block_prototype, profile, request.db)

			changed = True

		else:
			print('  existing')

			# Check if there are queues to be deleted
			for src in existing['blocks'][block_uuid]['source_uuids']:
				if src not in content['source_uuids']:
					delete_queue(src, block_uuid, block_prototype, profile, request.db)
					changed = True

			# Check if there are queues to be added
			for src in content['source_uuids']:
				if src not in existing['blocks'][block_uuid]['source_uuids']:
					create_queue(src, block_uuid, block_prototype, profile, request.db)
					changed = True

			# If the queues stayed the same, check to see if any settings changed
			if not changed:
				try:
					comparer.assertEqual(content['settings'], existing['blocks'][block_uuid]['settings'])
				except Exception as e:
					print(e)
					changed = True

			# If something changed, stop the existing process
			if changed and not block_prototype['single_instance']:
				print('  changed. Stopping.')
				stop_block(block_uuid, circus_client)

		# If there is reason to, start the process
		if changed and not block_prototype['single_instance']:
			print('  changed. Starting.')
			start_block(block_uuid, content, block_prototype, circus_client)




	# Save the running profile we just executed for next time
	if existing:
		newprofi['_id'] = existing['_id']
	request.db['conf_profiles_running'].save(newprofi)




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
	return {'user': request.user}


@view_config(route_name='socketio_test',
             renderer='templates/socketio_test.jinja2')
def socketio_test (request):
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
	profile['deleted'] = False

	request.db['conf_profiles'].save(profile)

	return pyramid.httpexceptions.HTTPFound(location=request.route_url('editor', uuid=profile['uuid']))


################################################################################
### Editor Helpers                                                           ###
################################################################################

# Returns the profile if it checks out (exists and is owned by logged in user).
# Returns None if not.
def validate_profile_uuid (request, profile_uuid):
	query = {
		'uuid': profile_uuid,
		'_userid': str(request.user['_id'])
	}
	return request.db['conf_profiles'].find_one(query)

# Save a profile to the database
# Does many checks to ensure that the profile is valid and that the user
# isn't trying to do anything he/she shouldn't be.
def save_profile (request, data):
	try:
		# Make sure that we have exactly these required keys
		profile_valid_keys = set(['uuid', 'name', 'blocks', 'connections'])
		profile_actual_keys = set(data.keys())
		if profile_valid_keys != profile_actual_keys:
			print('Incorrect keys in the profile')
			return None

		# Check this profile is valid
		profile = validate_profile_uuid(request, data['uuid'])
		if not profile:
			print('Could not find the profile')
			return None

		# Make sure that we have only blocks that are already a part of the profile
		# and that the blocks are well formed
		block_valid_keys = ['uuid', 'type', 'top', 'left']
		for block in data['blocks']:
			valid_keys = set(block_valid_keys)
			block_prototype = gatd.blocks.blocks[block['type']]

			# Check that the correct parameter/setting keys are present
			if 'parameters' in block_prototype:
				for param in block_prototype['parameters']:
					valid_keys.add(param['key'])
					if param['key'] in block:
						if type(block[param['key']]) != str:
							print('Parameters must be strings')
							return None
					else:
						print('Missing parameter {}'.format(param['key']))
						return None

			if 'settings' in block_prototype:
				for setting in block_prototype['settings']:
					valid_keys.add(setting['key'])
					if setting['key'] in block:
						if type(block[setting['key']]) != str:
							print('Settings must be strings')
							return None
					else:
						print('Missing setting {}'.format(setting['key']))
						return None

			# Check that this block is already in the profile
			for pblock in profile['blocks']:
				if pblock['uuid'] == block['uuid'] and pblock['type'] == block['type']:
					break
			else:
				print('Block not already in profile')
				return None

			# Check that this block has exactly the correct set of keys
			actual_keys = set(block.keys())
			if valid_keys != actual_keys:
				print('Block has the wrong keys')
				return None

			# Verify that connection limits aren't violated
			if 'target_group_max_conn' in block_prototype:
				count = 0
				for connection in data['connections']:
					if connection['target_uuid'] == block['uuid']:
						count += 1
				if count > block_prototype['target_group_max_conn']:
					print('Too many target connections')
					return None
			if 'source_group_max_conn' in block_prototype:
				count = 0
				for connection in data['connections']:
					if connection['source_uuid'] == block['uuid']:
						count += 1
				if count > block_prototype['source_group_max_conn']:
					print('Too many source connections')
					return None


		# Check the connections
		for connection in data['connections']:
			# Verify the connection has exactly the correct keys
			valid_keys = set(['source_uuid', 'target_uuid'])
			actual_keys = set(connection.keys())
			if valid_keys != actual_keys:
				print('Wrong keys in connection')
				return None

			# Verify that each connection connects two valid blocks
			src = None
			dst = None
			for block in data['blocks']:
				if block['uuid'] == connection['source_uuid']:
					src = gatd.blocks.blocks[block['type']]
				elif block['uuid'] == connection['target_uuid']:
					dst = gatd.blocks.blocks[block['type']]
			if (not src) or (not dst):
				print('Invalid block connection')
				return None

			# Verify that those blocks are allowed to be connected
			if src['source_group'] != dst['target_group'] or\
			   (not src['source_group']) or (not dst['target_group']):
				print('Cannot connect these blocks.')
				return None


		# At this point the block checks out
		data['_userid'] = str(request.user['_id'])
		data['_id'] = profile['_id']
		request.db['conf_profiles'].save(data)

		return data

	except Exception as e:
		print(e)
		return None



@view_config(route_name='editor',
             renderer='templates/editor.jinja2',
             permission='loggedin')
def editor (request):

	block_buttons = [('Data Input', ['receiver_udp_ipv6',
									 'receiver_udp_ipv4',
									 'receiver_http_post',
									 'queryer_http_get']),
					 ('Receiver Helpers', ['deduplicator', 'queue_combine_a']),
					 ('Formatters', ['formatter_python',
					                 'formatter_contenttype',
					                 'formatter_json']),
					 ('Processors', ['processor_python', 'meta_keyvalue']),
					 ('Storage', ['database_mongodb']),
					 ('Viewers', ['streamer',
					              'viewer',
					              'queryer',
					              'replayer'])
					]

	profile_uuid = request.matchdict.get('uuid')
	profile = validate_profile_uuid(request, profile_uuid)

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


@view_config(route_name='editor_block',
             renderer='json',
             permission='loggedin')
def editor_block (request):
	block_name = request.matchdict['block']
	profile_uuid = request.matchdict['profile']

	print(profile_uuid)

	if block_name not in gatd.blocks.blocks:
		return {'status': 'error',
			'reason': 'Invalid block.'}

	profile = validate_profile_uuid(request, profile_uuid)
	if not profile:
		return {'status': 'error',
			'reason': 'Invalid profile.'}

	block = copy.deepcopy(gatd.blocks.blocks[block_name])
	block['type'] = block_name
	block['uuid'] = str(uuid.uuid4())
	block['top']  = 0
	block['left'] = 0

	profile = request.db['conf_profiles'].find_one({'uuid': profile_uuid})

	if block_name in block_parameters_fns:
		block_parameters_fns[block_name](profile, block)

	# Add the block to the profile. This is a little strange, but it can always
	# be deleted later. We do this so we can validate that all the data we
	# get from the client checks out.
	if 'blocks' not in profile:
		profile['blocks'] = []
	new_block = {}
	new_block['type'] = block['type']
	new_block['uuid'] = block['uuid']
	new_block['top']  = block['top']
	new_block['left'] = block['left']
	for param in gatd.blocks.blocks[block['type']].get('parameters', []):
		new_block[param['key']] = param.get('value', '')
	for setting in gatd.blocks.blocks[block['type']].get('settings', []):
		new_block[setting['key']] = setting.get('value', '')
	profile['blocks'].append(new_block)
	request.db['conf_profiles'].save(profile)

	# Return the block to the client so it can display it
	block_html = pyramid.renderers.render('templates/block_popup.jinja2', {'block': block})

	return {'block': block,
			'html': block_html,
			'status': 'success'}


@view_config(route_name='editor_save',
			 request_method='POST',
			 renderer='json',
			 permission='loggedin')
def editor_save (request):
	data = request.json_body

	profile = save_profile(request, data)

	if not profile:
		raise pyramid.httpexceptions.HTTPBadRequest()


@view_config(route_name='editor_saveupload',
			 request_method='POST',
			 renderer='json',
			 permission='loggedin')
def editor_saveupload (request):
	data = request.json_body

	profile = save_profile(request, data)

	if not profile:
		raise pyramid.httpexceptions.HTTPBadRequest()

	# After saving, run this profile.
	run_profile(request, profile)

	return {'status': 'success'}


@view_config(route_name='editor_meta_keyvalue',
			 renderer='templates/editor_meta_keyvalue.jinja2',
			 permission='loggedin')
def editor_meta_keyvalue (request):
	profile_uuid = request.matchdict['profile']
	block_uuid = request.matchdict['block']

	profile = request.db['conf_profiles'].find_one({'uuid': profile_uuid,
	                                                '_userid': str(request.user['_id'])})

	if not profile:
		return pyramid.httpexceptions.HTTPFound(location=request.route_url('profiles'))

	for block in profile['blocks']:
		if block['uuid'] == block_uuid and block['type'] == 'meta_keyvalue':
			# Get all the records for the key value pairs
			lines = list(request.db[block_uuid].find())

			return {
				'lines': lines,
				'profile': profile,
				'block': block
			}
	else:
		return pyramid.httpexceptions.HTTPFound(location=request.route_url('profiles'))






@view_config(route_name='editor_meta_keyvalue_save',
			 request_method='POST',
			 permission='loggedin')
def editor_meta_keyvalue_save (request):
	profile_uuid = request.POST['profile_uuid']
	block_uuid = request.POST['block_uuid']

	profile = validate_profile_uuid(request, profile_uuid)

	if not profile:
		return pyramid.httpexceptions.HTTPFound(location=request.route_url('profiles'))

	for block in profile['blocks']:
		if block['uuid'] == block_uuid and block['type'] == 'meta_keyvalue':

			# Get all the records for the key value pairs
			for k,v in request.POST.items():
				names = k.split('-')
				if len(names) == 4 and names[0] == 'new' and names[1] == 'query' and names[2] == 'key':
					query = None
					addits = []

					print(k)
					query_key = v
					query_value = request.POST['new-query-value-{}'.format(names[3])]
					query = (query_key, query_value)

					i = 0
					while True:
						k_name = 'new-addit-key-{}-{}'.format(names[3], i)
						v_name = 'new-addit-value-{}-{}'.format(names[3], i)

						try:
							addit_key = request.POST[k_name]
							addit_value = request.POST[v_name]
							addits.append((addit_key, addit_value))
						except:
							break

						i += 1

					request.db[block_uuid].insert({'query': query, 'additional': addits})

			# Kill the meta block so it gets restarted with the new data
			print('Kill {}'.format(block_uuid))
			circus_client = circus.client.CircusClient(endpoint='tcp://{host}:{port}'\
				.format(host=gatdConfig.circus.HOST, port=gatdConfig.circus.PORT))
			to_circus = {
				'command': 'signal',
				'properties': {
					'name': block_uuid,
					'signum': 9
				}
			}
			circus_client.call(to_circus)


			return pyramid.httpexceptions.HTTPFound(location=request.route_url('editor_meta_keyvalue',
				profile=profile_uuid, block=block_uuid))
	else:
		return pyramid.httpexceptions.HTTPFound(location=request.route_url('profiles'))








