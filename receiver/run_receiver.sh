#!/bin/bash

screen -S gatd-receiver-udp -m -d ./receiver-udp
screen -S gatd-receiver-tcp -m -d python receiver_tcp.py

