#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <sys/time.h>
#include <byteswap.h>

#include <amqp.h>
#include <amqp_framing.h>
#include "utils.h"

#include "receiver.h"

void receive_udp () {

	int                     socket_world;
	struct sockaddr_in6     recv_addr;
	struct in6_addr         recv_ipv6_addr = IN6ADDR_ANY_INIT;

	amqp_connection_state_t amqp_conn;
	amqp_bytes_t            amqp_message;

	struct message_item_t   message;

	int                     ret;

	// Setup
	message.type = PKT_TYPE_UDP;

	// Connect to RabbitMQ
	amqp_conn = amqp_connect();

	// Create an IPv6 ready socket
	socket_world = socket(AF_INET6, SOCK_DGRAM, 0);
	if (socket_world < 0) {
		fprintf(stderr, "Unable to create UDP socket\n");
		return;
	}

	// Bind the socket to the correct port on all interfaces
	recv_addr.sin6_family = AF_INET6;
	recv_addr.sin6_addr   = recv_ipv6_addr;
	recv_addr.sin6_port   = htons(UDP_RECEIVE_PORT);

	ret = bind(socket_world, (struct sockaddr*) &recv_addr, sizeof(recv_addr));

	if (ret < 0) {
		// error on binding
		fprintf(stderr, "Unable to bind UDP socket\n");
		return;
	}

	printf("starting receive\n");

	// Receive
	while (1) {
		uint8_t             buffer[MAX_INCOMING_LENGTH];
		struct sockaddr_in6 sender_addr;
		uint32_t            sender_addr_len;
		int32_t             packet_len;
		int32_t             stored_len;

		packet_len = recvfrom(socket_world,
		                      buffer,
		                      MAX_INCOMING_LENGTH,
		                      0,
		                      (struct sockaddr*) &sender_addr,
		                      &sender_addr_len);

		if (packet_len > -1) {
			message.time = bswap_64(get_time());
			message.port = sender_addr.sin6_port;
			stored_len   = min(packet_len, MAX_INCOMING_LENGTH);
			memcpy(&message.addr, &sender_addr.sin6_addr, sizeof(struct in6_addr));
			memcpy(&message.data, buffer, stored_len);

			amqp_message.len   = MESSAGE_ITEM_BASE_SIZE + stored_len;
			amqp_message.bytes = &message;

			// Publish
			ret = amqp_basic_publish(amqp_conn,
			                         amqp_channel,
			                         amqp_exchange,
			                         amqp_routing_key,
			                         0,
			                         0,
			                         NULL,
			                         amqp_message);
		}

	}

	close(socket_world);

	amqp_channel_close(amqp_conn, 1, AMQP_REPLY_SUCCESS);
	amqp_connection_close(amqp_conn, AMQP_REPLY_SUCCESS);
	amqp_destroy_connection(amqp_conn);
}

