from pyramid.config import Configurator
import pyramid.session
import pyramid.authentication
import pyramid.authorization
import pyramid.security

import urllib.parse

import bson.objectid
import pymongo

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



	authorization_policy = pyramid.authorization.ACLAuthorizationPolicy()
	authn_policy = pyramid.authentication.AuthTktAuthenticationPolicy(
           config.registry.settings['pyramid.auth.secret'],
           callback=get_permission,
           hashalg='sha512')
	config.set_authentication_policy(authn_policy)
	config.set_authorization_policy(authorization_policy)



	config.add_route('home', '/')

	config.add_route('login', '/login/{provider_name}')

	config.add_route('profiles',    '/profiles')
	config.add_route('profile_new', '/profile/new')


	config.add_route('editor_block', '/editor/block/{block}')
	config.add_route('editor_save',  '/editor/save')
	config.add_route('editor',       '/editor/{uuid}')

	config.scan()
	return config.make_wsgi_app()
