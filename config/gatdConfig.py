#
# This module converts a text config file to python classes and attributes.
#
# so in gatd.config:
#
#  [mongo]
#  host: inductor.eecs.umich.edu
#
# becomes, in Python,:
#
#  gatdConfig.mongo.HOST
#


import ConfigParser
import os
import sys

class BaseConfigSection (object):
	def __getattr__ (self, name):
		print('')
		print('Could not find the proper key in gatd.config')
		print('Do you have the latest copy of gatd.config?')
		print('')
		raise AttributeError('error: {}'.format(name))


CONFIG_FILENAME = 'gatd.config'

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         CONFIG_FILENAME))

for section in config.sections():
	attrs = dict(config.items(section))

	# Convert integers to integers
	for attr in attrs:
		try:
			attrs[attr] = int(attrs[attr])
		except ValueError:
			pass

	lattrs = dict((k.upper(), v) for k, v in attrs.iteritems())
	newclass = type(section, (BaseConfigSection,), lattrs)

	setattr(sys.modules[__name__], section, newclass())
