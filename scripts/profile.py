#!/usr/bin/env python2

import argparse
import os
import random
import string
import sys

sys.path.append(os.path.abspath('../formatter'))
sys.path.append(os.path.abspath('../config'))
import MongoInterface


info = """This script has tools for dealing with profiles.

Right now it will give you a new Profile ID or list an existing
Profile ID.

Profile IDs are 10 character strings
consisting of lower and uppercase letters and numbers.
Profile IDs are linked with the class name of the parser
(formatter) that will handle the incoming packets.
"""

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

def createProfileId ():
	pid = ''.join(random.choice(string.letters + string.digits) for x in range(10))
	return pid


m = MongoInterface.MongoInterface()

parser = argparse.ArgumentParser(description=info)
parser.add_argument('--parser',
                    required=True,
                    help='class name of the parser (formatter) that will \
handle the packets. Example: "temperatureParser"')

args = parser.parse_args()


dbinfo = m.getProfileByParser(args.parser)

if dbinfo:
	print('Profile ID: {}'.format(dbinfo['profile_id']))
else:
	print('No Profile ID found for that parser.')
	if confirm('Create new Profile ID for {}?'.format(args.parser)):
		pid = createProfileId()
		m.addProfile(args.parser, pid, {})
		print('Added Profile ID {} for {}'.format(pid, args.parser))
