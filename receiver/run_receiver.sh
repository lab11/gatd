#!/bin/bash

screen -S gatd-receiver-udp -m -d ./receiver-udp.py
#screen -S gatd-receiver-udp -m -d ./receiver-udp
screen -S gatd-receiver-tcp -m -d ./receiver_tcp.py
screen -S gatd-receiver-http-post -m -d ./receiver_http_post.py
