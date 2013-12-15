#!/usr/bin/env python

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
	req_key = raw_input('Required key: ')
	if req_key == '':
		quit()
	m.setMetaRequiredKey(pids[cidx], req_key)

metas = m.getRawMeta(pids[cidx])


print(DSTR_T.format(req_key, 'QUERY', 'ADDITIONAL'))

i=-1
for i, meta in zip(range(len(metas)), metas):
	print(DSTR.format(i, meta[req_key], meta['query'], meta['additional']))

print('[{:>3d}] Add new'.format(i+1))


midx = int(raw_input('Index: '))
if midx >= len(metas):
	# add new
	req_key_val = raw_input('{}: '.format(req_key))
	print('QUERY')
	query = {}
	while True:
		k = raw_input('key: ')
		v = raw_input('val: ')
		if k == '' or v == '':
			break
		query[k] = v

	print('ADDITIONAL')
	addit = {}
	while True:
		k = raw_input('key: ')
		v = raw_input('val: ')
		if k == '' or v == '':
			break
		addit[k] = v

	print('\nAdding:\n')
	print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))
	print(DSTR_A.format(req_key_val, query, addit))
	print('')

	while True:
		confirm = raw_input('Add it?: ')
		if confirm == '':
			continue
		if 'y' in confirm:
			#add it
			m.addMeta(pid=pids[cidx],
			          req_key=req_key,
			          req_key_value=req_key_val,
			          query=query,
			          additional=addit)
		break

else:
	# Update
	req_key_val = raw_input('{} [{}]: '.format(req_key, metas[midx][req_key]))
	if req_key_val == '':
		req_key_val = metas[midx][req_key]










