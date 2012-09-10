C_FILES = receiver_udp.c receiver_tcp.c receiver.c utils.c


all:	$(C_FILES)
		gcc -Wall -Werror -pthread -O3 $(C_FILES) -o receiver -lrabbitmq

udp:	all
		screen -S gatd-receiver-udp -d -m ./receiver udp

tcp:	all
		screen -S gatd-receiver-tcp -d -m ./receiver tcp
