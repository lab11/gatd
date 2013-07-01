#!/bin/bash

screen -L -S gatd-streamer-tcp -d -m python streamer_tcp.py | tee -a streamer-tcp.log

