#!/usr/bin/env python2

import os
import sys

sys.path.append(os.path.abspath('../formatter'))
sys.path.append(os.path.abspath('../config'))
import MongoInterface

import edit_item

def strip (d):
	if '' in d:
		del d['']

def confirm (prompt, default=False):
	default_chr = 'y' if default else 'n'

	while True:
		resp = raw_input('{} [{}]: '.format(prompt, default_chr)).strip().lower()

		# If nothing was entered then just return whatever is the default
		if not resp:
			return default

		if resp in ['y', 'ye', 'yes', 'true']:
			return True
		elif resp in ['n', 'no', 'false']:
			return False

		print('Bad response. Try again.')



def edit_meta (req_key, req_key_val, query, addit):
	while True:
		req_key_val, query, addit = edit_item.edit_meta(req_key,
		                                                req_key_val,
		                                                query,
		                                                addit)
		strip(query)
		strip(addit)
		print('\nMeta Record:')
		print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))
		print(DSTR_A.format(req_key_val, query, addit))
		if not confirm('Continue editing?'):
			break
	return (req_key_val, query, addit)


DSTR_T = '[idx] {:<25s} {:<20s} {:<50s}'
DSTR   = '[{:>3d}] {:<25s} {:<20s} {:<50s}'

DSTR_A = '      {:<25s} {:<20s} {:<50s}'

pids = []

m = MongoInterface.MongoInterface()


configs = m.getAllProfiles()

print('Choose which profile you want:')
for i, c in zip(range(len(configs)), configs):
	pids.append(c['profile_id'])
	print('[{:>3d}] {}'.format(i, c['parser_name']))
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

	if confirm('Add it?', True):
		m.addMeta(pid=pids[cidx],
		          req_key=req_key,
		          req_key_value=req_key_val,
		          query=query,
		          additional=addit)

else:

	meta = metas[midx]

	print('\nWorking on:')
	print(DSTR_A.format(req_key, 'QUERY', 'ADDITIONAL'))
	print(DSTR_A.format(meta[req_key], meta['query'], meta['additional']))
	print('')

	if confirm('Delete?', False):
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








