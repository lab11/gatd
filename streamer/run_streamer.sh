#!/bin/bash

screen -L -S gatd-streamer-socketio -d -m forever streamer_socketio.js | tee -a streamer-socketio.log
screen -L -S gatd-streamer-tcp -d -m ./streamer_tcp.py | tee -a streamer-tcp.log
screen -L -S gatd-streamer-socketiopy -d -m ./streamer_socketio.py | tee -a streamer-socketiopy.log
screen -L -S gatd-streamer-socketiopyhist -d -m ./streamer_socketio_historical.py | tee -a streamer-socketiopyhist.log
