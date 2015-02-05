import logging
import sys

import logstash

import gatdConfig

def gatd_logger (name):
	l = logging.getLogger(name)
	l.setLevel(logging.DEBUG)
	l.addHandler(logstash.TCPLogstashHandler(gatdConfig.log.HOST, gatdConfig.log.PORT, version=1))
	return l

setattr(sys.modules[__name__], 'getLogger', gatd_logger)
