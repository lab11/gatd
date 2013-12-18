#!/usr/bin/env python

import meta_test
import MongoInterface
import gatdConfig
import sys


def strip (d):
	if '' in d:
		del d['']


def edit_meta (req_key, req_key_val, query, addit):
	while True:
		req_key_val, query, addit = meta_test.edit_meta(req_key,
		                                                req_key_val,
		                                                query,
		                                                addit)
		strip(query)
		strip(addit)
		print('\nMeta Record:')
		print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))
		print(DSTR_A.format(req_key_val, query, addit))
		choice = raw_input('Continue editing?: ')
		if choice == '':
			break
	return (req_key_val, query, addit)


DSTR_T = '[idx] {:<25s} {:<20s} {:<50s}'
DSTR   = '[{:>3d}] {:<25s} {:<20s} {:<50s}'

DSTR_A = '      {:<25s} {:<20s} {:<50s}'

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

try:
	midx = int(raw_input('Index: '))
except ValueError:
	sys.exit(0)

if midx >= len(metas):
	# add new
	req_key_val, query, addit = edit_meta(req_key, '', {}, {})

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

	meta = metas[midx]

	print('\nWorking on:')
	print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))
	print(DSTR_A.format(meta[req_key], meta['query'], meta['additional']))
	print('')

	confirm = raw_input('Delete?: ')
	if 'y' in confirm:
		m.deleteMeta(meta['_id'])
	else:
		req_key_val, query, addit = edit_meta(req_key,
		                                      meta[req_key],
		                                      meta['query'],
		                                      meta['additional'])

		m.updateMeta(dbid=meta['_id'],
		             pid=meta['profile_id'],
		             req_key=req_key,
		             req_key_value=req_key_val,
		             query=query,
		             additional=addit)
		print('Updated.')








