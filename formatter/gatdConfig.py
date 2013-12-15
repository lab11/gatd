#
# Functions to retrieve configuration for GATD
#

import ConfigParser

config = ConfigParser.ConfigParser()
config.read('../config/gatd.config')


def getMongoHost():
	return config.get('mongo', 'host')

def getMongoPort():
	return config.getint('mongo', 'port')

def getMongoUsername():
	return config.get('mongo', 'username')

def getMongoPassword():
	return config.get('mongo', 'password')

