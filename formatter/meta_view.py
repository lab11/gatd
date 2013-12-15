#!/usr/bin/env python

import MongoInterface
import gatdConfig


pids = []

m = MongoInterface.MongoInterface(host=gatdConfig.getMongoHost(),
                                  port=gatdConfig.getMongoPort(),
                                  username=gatdConfig.getMongoUsername(),
                                  password=gatdConfig.getMongoPassword())


configs = m.getConfigs()

print('Choose which profile you want:')
for i, c in zip(range(len(configs)), configs):
	pids.append(c['profile_id'])
	print('[{:>3d}] {}'.format(i, c['name']))
cidx = int(raw_input('Index: '))
print('')

req_key = m.getMetaRequiredKey(pids[cidx])
metas = m.getRawMeta(pids[cidx])


print('{:<25s} {:<50s} {:<50s}'.format(req_key, 'QUERY', 'ADDITIONAL'))
for m in metas:
	print('{:<25s} {:<50s} {:<50s}'.format(m[req_key], m['query'], m['additional']))


