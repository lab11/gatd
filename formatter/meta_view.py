#!/usr/bin/env python

import MongoInterface

MONGO_HOST  = 'inductor.eecs.umich.edu'
MONGO_PORT  = 19000

pids = []

m = MongoInterface.MongoInterface(host=MONGO_HOST, port=MONGO_PORT)


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


