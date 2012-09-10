#!/bin/bash

screen -L -S gatd-streamer -d -m forever streamer.js | tee -a streamer.log

