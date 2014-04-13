#!/usr/bin/env python2

import os
import pymongo
import sys
import time

sys.path.append(os.path.abspath('../config'))
import gatdConfig

# Create a connection to the gatd server
mongo_conn = pymongo.MongoClient(host=gatdConfig.mongo.HOST,
                                 port=gatdConfig.mongo.PORT)
# Create the database for gatd if it doesn't exist already
mongo_db = mongo_conn[gatdConfig.mongo.DATABASE]
# Create a user for this database
mongo_db.add_user(name=gatdConfig.mongo.USERNAME,
                  password=gatdConfig.mongo.PASSWORD)

# Create all of the collections needed
mongo_db.create_collection(name=gatdConfig.mongo.COL_FORMATTED)
mongo_db.create_collection(name=gatdConfig.mongo.COL_FORMATTED_CAPPED,
                           capped=True,
                           size=536870912) # 0.5 GB in bytes
mongo_db.create_collection(name=gatdConfig.mongo.COL_UNFORMATTED)
mongo_db.create_collection(name=gatdConfig.mongo.COL_CONFIG)
mongo_db.create_collection(name=gatdConfig.mongo.COL_META_CONFIG)
mongo_db.create_collection(name=gatdConfig.mongo.COL_META)
mongo_db.create_collection(name=gatdConfig.mongo.COL_GATEWAY)
mongo_db.create_collection(name=gatdConfig.mongo.COL_EXPLORE_KEYS)

mongo_conn.close()
