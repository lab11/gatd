#ifndef __RECEIVER_UDP_H__
#define __RECEIVER_UDP_H__

#include <stdlib.h>

#include <amqp.h>
#include <amqp_framing.h>
#include "utils.h"


#define UDP_RECEIVE_PORT 4001
#define PKT_TYPE_UDP 0

extern const char           amqp_hostname[];
extern const int            amqp_port;
extern const char           amqp_username[];
extern const char           amqp_password[];
extern const amqp_bytes_t   amqp_exchange;
extern const amqp_bytes_t   amqp_routing_key;
extern const amqp_channel_t amqp_channel;

extern const int MESSAGE_ITEM_BASE_SIZE;


amqp_connection_state_t amqp_connect ();
uint64_t get_time ();
uint32_t min (uint32_t a, uint32_t b);

#endif
