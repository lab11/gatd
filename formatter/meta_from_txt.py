#!/usr/bin/env python

import sys

import MongoInterface
import gatdConfig


DSTR_T = '[idx] {:<25s} {:<50s} {:<50s}'
DSTR   = '[{:>3d}] {:<25s} {:<50s} {:<50s}'

DSTR_A = '{:<25s} {:<50s} {:<50s}'

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

if req_key == None:
	print('Need to set the required key')
	quit()

filename = sys.argv[1]

inserts = []

with open(filename) as f:
	for l in f:
		items = l.split('\t')
		if len(items) < 3:
			continue

		insert = {req_key:None,
			      'query':{},
			      'additional':{'location_str':None,
			                    'description':None}
			      }
		for item in items:
			if len(item) > 1:
				item = item.strip()
				if insert[req_key] == None:
					insert[req_key] = item
				elif insert['additional']['description'] == None:
					insert['additional']['description'] = item
				elif insert['additional']['location_str'] == None:
					insert['additional']['location_str'] = item
					inserts.append(insert)
					break

print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))

for insert in inserts:
	print(DSTR_A.format(insert[req_key], insert['query'], insert['additional']))

while True:
	confirm = raw_input('Add them?: ')
	if confirm == '':
		continue
	if 'y' in confirm:
		break
	else:
		quit()

for insert in inserts:
	m.addMeta(pid=pids[cidx],
	          req_key=req_key,
	          req_key_value=insert[req_key],
	          query=insert['query'],
	          additional=insert['additional'])










