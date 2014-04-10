#!/usr/bin/env python2

import json
import os
import sys

sys.path.append(os.path.abspath('../config'))
sys.path.append(os.path.abspath('../formatter'))
import MongoInterface

import edit_tree

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


def print_keys (indent, key_list):
	indent_str = ' '*indent

	if not key_list:
		return

	for k in key_list:
		print('{}{}'.format(indent_str, k['key']))
		print_keys(indent+4, k['children'])


def parseNewTree (lines, thislist, indent):

	print(lines)

	i = 0

	while i < len(lines):

		line = lines[i]


		lineindent = 0
		for c in line:
			if c == ' ':
				lineindent += 1
			else:
				break

		print('indent: {} lineindent: {} line: {}'.format(indent,lineindent,line))

		if lineindent == indent:
			thislist.append({'key': line.strip(), 'children': []})
			i += 1

		elif lineindent > indent:
			i += parseNewTree(lines[i:], thislist[-1]['children'], lineindent)

		else:
			return i
	return i




DSTR_T = '[idx] {:<25s} {:<20s} {:<50s}'
DSTR   = '[{:>3d}] {:<25s} {:<20s} {:<50s}'

DSTR_A = '      {:<25s} {:<20s} {:<50s}'

pids = []



m = MongoInterface.MongoInterface()

dbkeys = m.getExploreKeys()

for pidkeys in dbkeys:
	name = m.getConfigByProfileId(pidkeys['profile_id'])

	print('Profile ID: {}'.format(pidkeys['profile_id']))
	print('Profile Name: {}'.format(name['parser_name']))

	keys = json.loads(pidkeys['keys_json'])

	print_keys(4, keys)


	print('')
	print('')

	newtreetxt = edit_tree.edit_tree(keys)

	print(newtreetxt)

	new_tree = []

	parseNewTree(newtreetxt.strip().split('\n'), new_tree, 0)

	print(new_tree)


	print_keys(4, new_tree)



	quit()


