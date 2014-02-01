#!/bin/bash

screen -S gatd-receiver-udp -m -d ./receiver-udp
screen -S gatd-receiver-tcp -m -d python2 receiver_tcp.py
screen -S gatd-receiver-http-post -m -d python2 receiver_http_post.py
