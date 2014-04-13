#!/usr/bin/env python2

import glob
import os
import subprocess
import sys

sys.path.append(os.path.abspath('../config'))
import gatdConfig

cmd = 'screen -S gatd-processor-{name}  -d -m ./processor.py {name}'

externals_path = os.path.join(gatdConfig.gatd.EXTERNALS_ROOT,
                              gatdConfig.processor.EXTERNALS_PROCESSORS)

for processor in glob.glob(os.path.join(externals_path, '*.py')):
	path,ext = os.path.splitext(processor)
	filename = os.path.basename(path)

	if filename[0] != '_':
		name = filename.replace('_', '-')
		run_cmd = cmd.format(name=name)

		subprocess.call(run_cmd.split())
