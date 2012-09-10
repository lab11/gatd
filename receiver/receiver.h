#ifndef __H_RECEIVER__
#define __H_RECEIVER__

#include <stdlib.h>
#include <arpa/inet.h>

#include <amqp.h>
#include <amqp_framing.h>
#include "utils.h"


#define UDP_RECEIVE_PORT 4001
#define TCP_RECEIVE_PORT 4002

#define MAX_INCOMING_LENGTH 4096

#define PKT_TYPE_UDP 0
#define PKT_TYPE_TCP 1

struct message_item_t {
	uint8_t         type;   // 8 bits to identify the structure of this packet in case it changes
	struct in6_addr addr;   // IPv6 address of the sender
	uint16_t        port;   // Sender port
	uint64_t        time;   // Time packet was received
	uint8_t         data[MAX_INCOMING_LENGTH];
} __attribute__((__packed__));
typedef struct message_item_t message_item_t;


extern const char         amqp_hostname[];
extern const int          amqp_port;
extern const char         amqp_username[];
extern const char         amqp_password[];
extern const amqp_bytes_t amqp_exchange;
extern const amqp_bytes_t amqp_routing_key;

extern const int          MESSAGE_ITEM_BASE_SIZE;


amqp_connection_state_t amqp_connect ();
uint64_t get_time ();
uint32_t min (uint32_t a, uint32_t b);

void receive_udp ();
void receive_tcp ();

#endif
