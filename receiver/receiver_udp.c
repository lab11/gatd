#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <sys/time.h>
#include <byteswap.h>
#include <sys/socket.h>
#include <unistd.h>

#include <amqp.h>
#include <amqp_framing.h>
#include <amqp_tcp_socket.h>
#include "utils.h"

#include "receiver.h"
#include "receiver_udp.h"

// Global constants
const char           amqp_hostname[]    = "localhost";
const int            amqp_port          = 5672;
const char           amqp_username[]    = "guest";
const char           amqp_password[]    = "guest";
const amqp_channel_t amqp_channel       = 1;
const amqp_bytes_t   amqp_exchange      = {16, "receive_exchange"};
const amqp_bytes_t   amqp_exchange_type = {6, "fanout"};
const amqp_bytes_t   amqp_queue         = {13, "receive_queue"};
const amqp_bytes_t   amqp_routing_key   = {0, "\0"};
const amqp_table_t   amqp_table_null    = {0, NULL};
const amqp_boolean_t amqp_false         = 0;
const amqp_boolean_t amqp_true          = 1;

const int MESSAGE_ITEM_BASE_SIZE = sizeof(message_item_t) - MAX_INCOMING_LENGTH;


amqp_connection_state_t amqp_connect () {
	amqp_socket_t*          amqp_socket = NULL;
	amqp_connection_state_t amqp_conn;
	amqp_rpc_reply_t        amqp_ret;
	int                     result;

	amqp_conn = amqp_new_connection();

	amqp_socket = amqp_tcp_socket_new(amqp_conn);
	if (amqp_socket == 0) {
		fprintf(stderr, "Could not create amqp socket.\n");
		exit(1);
	}

	result = amqp_socket_open(amqp_socket, amqp_hostname, amqp_port);
	if (result) {
		fprintf(stderr, "Could not open amqp socket.\n");
		exit(1);
	}

	amqp_ret = amqp_login(amqp_conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN,
	                      amqp_username, amqp_password);
	die_on_amqp_error(amqp_ret, "Logging in");
	amqp_channel_open(amqp_conn, amqp_channel);
	amqp_ret = amqp_get_rpc_reply(amqp_conn);
	die_on_amqp_error(amqp_ret, "Opening channel");

	// Make sure the receiver exchange exists
	amqp_exchange_declare(amqp_conn, amqp_channel, amqp_exchange,
	                      amqp_exchange_type, amqp_false, amqp_true,
	                      amqp_table_null);

	// Make sure there is a queue bound to the exchange to receive the packets
	amqp_queue_declare(amqp_conn, amqp_channel, amqp_queue, amqp_false,
	                   amqp_true, amqp_false, amqp_false, amqp_table_null);

	// Bind the receive queue to the receive exchange
	amqp_queue_bind(amqp_conn, amqp_channel, amqp_queue, amqp_exchange,
	                amqp_routing_key, amqp_table_null);

	return amqp_conn;
}

// Return the current time in milliseconds from the unix epoch
uint64_t get_time () {
	struct timeval tv;
	uint64_t       time;

	if (gettimeofday(&tv, NULL) == 0) {
		time = ((uint64_t) tv.tv_sec) * 1000;
		time += ((uint64_t) tv.tv_usec) / 1000;
	} else {
		fprintf(stderr, "Could not get time properly.\n");
		exit(1);
	}

	return time;
}

uint32_t min (uint32_t a, uint32_t b) {
	if (a < b) return a;
	return b;
}

int main (int argc, char** argv) {
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
		return 1;
	}

	// Bind the socket to the correct port on all interfaces
	recv_addr.sin6_family = AF_INET6;
	recv_addr.sin6_addr   = recv_ipv6_addr;
	recv_addr.sin6_port   = htons(UDP_RECEIVE_PORT);

	ret = bind(socket_world, (struct sockaddr*) &recv_addr, sizeof(recv_addr));

	if (ret < 0) {
		// error on binding
		fprintf(stderr, "Unable to bind UDP socket\n");
		return 1;
	}

	printf("Beginning loop to receive UDP packets.\n");

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
			memcpy(&message.addr, &sender_addr.sin6_addr,
			       sizeof(struct in6_addr));
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

	return 0;

}
