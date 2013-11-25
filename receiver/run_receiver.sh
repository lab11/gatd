#!/bin/bash

screen -S gatd-receiver-udp -m -d ./receiver-udp
screen -S gatd-receiver-tcp -m -d python receiver_tcp.py
screen -S gatd-receiver-udp-ipv4 -m -d python receiver_udp_ipv6_over_ipv4.py
screen -S gatd-receiver-http-post -m -d python receiver_http_post.py
