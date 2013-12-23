#!/usr/bin/env python

import IPy

import meta_test
import MongoInterface
import sys


def strip (d):
	if '' in d:
		del d['']


def edit_gateway (prefix, addit):
	while True:
		prefix, addit = meta_test.edit_gateway_key(prefix, addit)
		strip(addit)
		print('\nGateway Record:')
		print(DSTR_A.format('PREFIX', 'ADDITIONAL'))
		print(DSTR_A.format(prefix, addit))
		choice = raw_input('Continue editing?: ')
		if choice == '':
			break
	return (prefix, addit)


DSTR_T = '[idx] {:<30s} {:<50s}'
DSTR   = '[{:>3d}] {:<30s} {:<50s}'

DSTR_A = '      {:<30s} {:<50s}'

pids = []

m = MongoInterface.MongoInterface()

gws = m.getRawGatewayKeys()

print(DSTR_T.format('PREFIX', 'ADDITIONAL'))

i=-1
for i, gw in zip(range(len(gws)), gws):
	print(DSTR.format(i, gw['prefix_cidr'], gw['additional']))

print('[{:>3d}] Add new'.format(i+1))

try:
	midx = int(raw_input('Index: '))
except ValueError:
	sys.exit(0)

if midx >= len(gws):
	# add new
	prefix, addit = edit_gateway('', {})

	print('\nAdding:\n')
	print(DSTR_A.format('PREFIX', 'ADDITIONAL'))
	print(DSTR_A.format(prefix, addit))
	print('')

	while True:
		confirm = raw_input('Add it?: ')
		if confirm == '':
			continue
		if 'y' in confirm:
			#add it
			prefix_int = IPy.IP(prefix).int() >> 64
			m.addGatewayKeys(prefix=prefix_int,
			                 additional=addit)
		break

else:

	gw = gws[midx]

	print('\nWorking on:')
	print(DSTR_A.format('PREFIX', 'ADDITIONAL'))
	print(DSTR_A.format(gw['prefix_cidr'], gw['additional']))
	print('')

	confirm = raw_input('Delete?: ')
	if 'y' in confirm:
		m.deleteGatewayKey(gw['_id'])
	else:
		prefix, addit = edit_gateway(gw['prefix_cidr'], gw['additional'])

		m.updateGatewayKeys(dbid=gw['_id'],
		                   prefix=IPy.IP(prefix).int() >> 64,
		                   additional=addit)
		print('Updated.')








