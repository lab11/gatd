Receiver Service
================

The receiver is the incoming portal to GATD. All data must be sent
to a reciver. Different receivers run on different ports using different
protocols. 


Receiver to Formatter API
-------------------------

Each receiver must send a packed struct of data to the formatter. The format
must match the following C struct:

    struct message_item_t {
        uint8_t         type;   // 8 bits to identify the structure of this packet
                                //  in case it changes
        struct in6_addr addr;   // IPv6 address of the sender
        uint16_t        port;   // Sender port
        uint64_t        time;   // Time packet was received in milliseconds
        uint8_t         data[MAX_INCOMING_LENGTH];
    };

Each receiver must have its own type. The time is recorded in milliseconds since
the Unix epoch.


Available Receivers
-------------------

### UDP

To use this receiver simply send UDP packets to the server. The entire body
of the UDP packet will be stored. The port that GATD listens on for
UDP packets is set in `gatd.config`.

The UDP listener records the IPv6 address of the source (this will work
for IPv4 devices as well), the source port, and the time when the packet
was received.

### TCP

To use this receiver simply create a TCP connection to the server and send
data to the server.

This receiver is not particularly well implemented currently and requires
sufficient time between data being sent over the connection to ensure
separate packets are decoded properly.

### HTTP Post

This receiver listens for HTTP POST requests. The URL should look like:

    http://host/<profile_id>?arg1=val1&arg2=val2

The `profile_id` as the post file is how the packets are categorized by GATD.

GATD will automatically convert the URL string into JSON.
