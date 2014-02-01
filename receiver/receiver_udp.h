#ifndef __RECEIVER_UDP_H__
#define __RECEIVER_UDP_H__

#include <stdlib.h>

#include <amqp.h>
#include <amqp_framing.h>
#include "utils.h"

extern const int MESSAGE_ITEM_BASE_SIZE;


amqp_connection_state_t amqp_connect ();
uint64_t get_time ();
uint32_t min (uint32_t a, uint32_t b);

#endif
