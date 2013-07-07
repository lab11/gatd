#!/bin/bash

screen -L -S gatd-streamer-socketio -d -m forever streamer_socketio.js | tee -a streamer-socketio.log
screen -L -S gatd-streamer-tcp -d -m python streamer_tcp.py | tee -a streamer-tcp.log

