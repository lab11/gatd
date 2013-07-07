#ifndef __RECEIVER_H__
#define __RECEIVER_H__

#include <stdlib.h>
#include <arpa/inet.h>

struct message_item_t {
	uint8_t         type;   // 8 bits to identify the structure of this packet
	                        //  in case it changes
	struct in6_addr addr;   // IPv6 address of the sender
	uint16_t        port;   // Sender port
	uint64_t        time;   // Time packet was received
	uint8_t         data[MAX_INCOMING_LENGTH];
} __attribute__((__packed__));
typedef struct message_item_t message_item_t;

#endif
