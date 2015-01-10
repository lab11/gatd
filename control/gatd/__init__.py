from pyramid.config import Configurator
import pyramid.session
import pyramid.authentication
import pyramid.authorization
import pyramid.security

import os
import sys
import urllib.parse

import bson.objectid
import circus.client
import pika
import pymongo

import gatd.blocks
import gatd.views

sys.path.append(os.path.abspath('../gatd'))
import gatdConfig

class RootFactory ():
    __name__ = None
    __parent__ = None
    __acl__ = [
        (pyramid.security.Allow, 'loggedin', 'loggedin'),
    ]

    def __init__(self, request):
        pass

def get_permission (userid, request):
	return ['loggedin']



def init_exchanges ():
	exchanges = [
		'xch_scope_a',
		'xch_scope_b',
	]

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

	for exchange in exchanges:
			amqp_chan.exchange_declare(exchange=exchange,
			                           exchange_type='direct',
			                           durable='true')
	amqp_chan.close()

def init_profiles (db):
	circus_client = circus.client.CircusClient(endpoint='tcp://{host}:{port}'\
		.format(host=gatdConfig.circus.HOST, port=gatdConfig.circus.PORT))

	# Get the state that is supposed to exist
	profile_cursor = db['conf_profiles_running'].find()

	for profile in profile_cursor:

		if profile['uuid'] != '89626667-443e-4cd7-bdde-8039e2254467':
			print('Not this profile')
			continue

		print('start it')

		for block_uuid,content in profile['blocks'].items():

			block_prototype = gatd.blocks.blocks[content['type']]
			if block_prototype['single_instance']:
				continue

			exists = gatd.views.query_block_exists(block_uuid, circus_client)

			if not exists:
				block_prototype = gatd.blocks.blocks[content['type']]
				gatd.views.start_block(block_uuid, content, block_prototype, circus_client)





def main(global_config, **settings):
	""" This function returns a Pyramid WSGI application.
	"""
	config = Configurator(settings=settings, root_factory='gatd.RootFactory')
	config.include('pyramid_jinja2')
	config.add_static_view('static', 'static', cache_max_age=3600)
	# session_factory = pyramid.session.UnencryptedCookieSessionFactoryConfig('thisisasecret')
	# config = Configurator(settings=settings,
	# 	session_factory=session_factory,
	# 	autocommit=True)


	db_url = urllib.parse.urlparse(settings['mongo_uri'])
	config.registry.db = pymongo.Connection(
		host=db_url.hostname,
		port=db_url.port,
	)

	def add_db(request):
		db = config.registry.db[db_url.path[1:]]
		if db_url.username and db_url.password:
			db.authenticate(db_url.username, db_url.password)
		return db
	config.add_request_method(add_db, 'db', reify=True)

	def add_user(request):
		login = pyramid.security.authenticated_userid(request)
		if not login:
			return None
		return request.db['conf_users'].find_one({'_id': bson.objectid.ObjectId(login)})
	config.add_request_method(add_user, 'user', reify=True)

	# Init the actual GATD components
	init_exchanges()
	init_profiles(add_db(None))

	authorization_policy = pyramid.authorization.ACLAuthorizationPolicy()
	authn_policy = pyramid.authentication.AuthTktAuthenticationPolicy(
           config.registry.settings['pyramid.auth.secret'],
           callback=get_permission,
           hashalg='sha512')
	config.set_authentication_policy(authn_policy)
	config.set_authorization_policy(authorization_policy)



	config.add_route('home', '/')

	config.add_route('login', '/login/{provider_name}')

	config.add_route('socketio_test', '/socketio/test')

	config.add_route('profiles',    '/profiles')
	config.add_route('profile_new', '/profile/new')


	config.add_route('editor_block',         '/editor/block/{profile}/{block}')
	config.add_route('editor_save',          '/editor/save')
	config.add_route('editor_saveupload',    '/editor/saveupload')
	config.add_route('editor_meta_keyvalue', '/editor/meta_keyvalue/{profile}/{block}')
	config.add_route('editor',               '/editor/{uuid}')

	config.scan()
	return config.make_wsgi_app()
