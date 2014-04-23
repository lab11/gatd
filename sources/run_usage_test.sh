#!/bin/bash

echo "Run the computer usage GATD test"

# Check if already running
SCREEN_OUT=`screen -ls`
if [[ "$SCREEN_OUT" =~ .*gatd-usage-test.* ]]; then
	echo "usage monitor already running"
	exit
fi

# Check if psutil is installed
echo "Checking if psutil is installed"
python3 -c "import psutil" > /dev/null 2> /dev/null

if [ "$?" -ne 0 ]; then
	# No psutil
	echo "psutil not installed"

	# Check for pip
	pip --version > /dev/null 2> /dev/null
	if [ "$?" -ne 0 ]; then
		# No pip
		echo "pip not installed"
		echo "installing psutil by source"
		wget http://psutil.googlecode.com/files/psutil-0.4.1.tar.gz
		tar xzf psutil-0.4.1.tar.gz
		cd psutil-0.4.1.tar.gz
		sudo python3 setup.py install
		if [ "$?" -ne 0 ]; then
			# didn't work, are you root
			echo "psutil failed to install"
			exit
		fi
		rm psutil-0.4.1.tar.gz
		rm -rf psutil-0.4.1

	else
		# Use pip
		echo "installing psutil with pip"
		sudo pip-python3 install psutil
		if [ "$?" -ne 0 ]; then
			# didn't work, are you root
			echo "psutil failed to install"
			exit
		fi

	fi

fi

screen -S gatd-usage-test -d -m python3 computer_stats_udp_source.py
if [ "$?" -ne 0 ]; then
	echo "usage monitor failed to start"
else
	echo "usage monitor successfully running"
fi

