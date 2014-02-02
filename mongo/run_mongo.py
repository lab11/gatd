#!/usr/bin/env python2

from sh import screen

sys.path.append(os.path.abspath('../config'))
import gatdConfig

screen('-S', 'mongodb', '-d', '-m', 'mongod', '--port', gatdConfig.mongo.PORT,
       '--auth')

