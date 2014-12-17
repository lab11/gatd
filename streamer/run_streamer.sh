#!/bin/bash

#screen -S gatd-streamer-socketio -d -m forever streamer_socketio.js
screen -S gatd-streamer-tcp -d -m ./streamer_tcp.py
screen -S gatd-streamer-socketio-py-base   -d -m ./streamer_socketio.py new
screen -S gatd-streamer-socketio-py-hist   -d -m ./streamer_socketio.py all
screen -S gatd-streamer-socketio-py-replay -d -m ./streamer_socketio.py replay
