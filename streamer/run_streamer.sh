#!/bin/bash

screen -L -S gatd-streamer-socketio -d -m forever streamer_socketio.js | tee -a streamer-socketio.log
screen -L -S gatd-streamer-tcp -d -m ./streamer_tcp.py | tee -a streamer-tcp.log
screen -L -S gatd-streamer-socketio-py -d -m ./streamer_socketio.py | tee -a streamer-socketiopy.log
screen -L -S gatd-streamer-socketio-py-hist -d -m ./streamer_socketio_historical.py | tee -a streamer-socketiopyhist.log
screen    -S gatd-streamer-socketio-py-replay -d -m ./streamer_socketio_replay.py
