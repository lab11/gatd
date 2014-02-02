#!/bin/bash

screen -L -S gatd-streamer-socketio -d -m forever streamer_socketio.js | tee -a streamer-socketio.log
screen -L -S gatd-streamer-tcp -d -m python2 streamer_tcp.py | tee -a streamer-tcp.log
screen -L -S gatd-streamer-socketiopy -d -m python2 streamer_socketio.py | tee -a streamer-socketiopy.log

