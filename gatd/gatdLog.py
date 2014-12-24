import os
import json
import logging
import logging.config
import sys

import gatdConfig

if os.path.exists(gatdConfig.log.CONFIG_FILE):
    with open(gatdConfig.log.CONFIG_FILE) as f:
        config = json.load(f)
        logging.config.dictConfig(config)
        print('log')
else:
    logging.basicConfig(level=logging.INFO)


setattr(sys.modules[__name__], 'getLogger', logging.getLogger)

# def setup_logging(
#     default_path='logging.json', 
#     default_level=logging.INFO,
#     env_key='LOG_CFG'
# ):
#     """Setup logging configuration

#     """
#     path = default_path
#     value = os.getenv(env_key, None)
#     if value:
#         path = value
#     if os.path.exists(path):
#         with open(path, 'rt') as f:
#             config = json.load(f)
#         logging.config.dictConfig(config)
#     else:
#         logging.basicConfig(level=default_level)