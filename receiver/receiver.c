#include <stdio.h>
//#include <stdlib.h>
#include <string.h>
#include <stdint.h>
//#include <unistd.h>
//#include <sys/types.h>
//#include <sys/socket.h>
//#include <netinet/in.h>
//#include <arpa/inet.h>
//#include <pthread.h>
#include <sys/time.h>
//#include <byteswap.h>

#include <amqp.h>
#include <amqp_framing.h>
#include "utils.h"

#include "receiver.h"

// Global constants
const char         amqp_hostname[]  = "localhost";
const int          amqp_port        = 5672;
const char         amqp_username[]  = "guest";
const char         amqp_password[]  = "guest";
const amqp_channel_t amqp_channel = 1;
const amqp_bytes_t amqp_exchange    = {16, "receive_exchange"};
const amqp_bytes_t amqp_exchange_type = {6, "fanout"};
const amqp_bytes_t amqp_queue = {13, "receive_queue"};
const amqp_bytes_t amqp_routing_key = {0, "\0"};
const amqp_table_t amqp_table_null = {0, NULL};
const amqp_boolean_t amqp_false = 0;
const amqp_boolean_t amqp_true = 1;

const int MESSAGE_ITEM_BASE_SIZE = sizeof(message_item_t) - MAX_INCOMING_LENGTH;


amqp_connection_state_t amqp_connect () {
	int                     socket_amqp;
	amqp_connection_state_t amqp_conn;
	amqp_rpc_reply_t        amqp_ret;

	amqp_conn   = amqp_new_connection();
	socket_amqp = amqp_open_socket(amqp_hostname, amqp_port);
	amqp_set_sockfd(amqp_conn, socket_amqp);
	amqp_ret    = amqp_login(amqp_conn, "/", 0, 131072, 0,
	                         AMQP_SASL_METHOD_PLAIN, amqp_username,
	                         amqp_password);
	die_on_amqp_error(amqp_ret, "Logging in");
	amqp_channel_open(amqp_conn, amqp_channel);
	amqp_ret    = amqp_get_rpc_reply(amqp_conn);
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

uint64_t get_time () {

	struct timeval tv;
	uint64_t       time;

	if (gettimeofday(&tv, NULL) == 0) {
		time = ((uint64_t) tv.tv_sec) * 1000;
		time += ((uint64_t) tv.tv_usec) / 1000;
	} else {
		fprintf(stderr, "Could not get time properly\n");
		exit(1);
	}

	return time;
}

uint32_t min (uint32_t a, uint32_t b) {
	if (a < b) return a;
	return b;
}

int main (int argc, char** argv) {

	if (argc < 2) {
		fprintf(stderr, "Usage: %s udp|tcp\n", argv[0]);
		return -1;
	}

	if (!strcmp(argv[1], "udp")) {
		// Use UDP
		receive_udp();

	} else if (!strcmp(argv[1], "tcp")) {
		// Use TCP
		receive_tcp();

	} else {
		fprintf(stderr, "Options are: udp|tcp\n");
		return -1;
	}

	return 0;

}
