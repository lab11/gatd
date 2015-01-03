import os
import json
import logging
import logging.config
import sys

import logging_tree

import gatdConfig

if os.path.exists(gatdConfig.log.CONFIG_FILE):
    with open(gatdConfig.log.CONFIG_FILE) as f:
        config = json.load(f)
        logging.config.dictConfig(config)
        logging_tree.printout()
else:
    logging.basicConfig(level=logging.INFO)

setattr(sys.modules[__name__], 'getLogger', logging.getLogger)
