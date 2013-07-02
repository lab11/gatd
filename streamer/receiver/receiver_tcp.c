#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <netdb.h>
#include <errno.h>

#include <json/json.h>

#define RCVBUFSIZE 32   /* Size of receive buffer */

#define HOST "inductor.eecs.umich.edu"
#define PORT "22500"

#define INBUF_SIZE 16384


char query[] = "{\"seq_no\":1}";
//char query[] = "{}";


int main (int argc, char *argv[]) {
	int s;
	struct addrinfo hints;
	struct addrinfo *strmSvr;
	int error;

	ssize_t send_len;
	ssize_t recv_len;
	char inbuf[INBUF_SIZE];

	json_object* data;


	// Tell getaddrinfo() that we only want a TCP connection
	memset(&hints, 0, sizeof(hints));
	hints.ai_socktype = SOCK_STREAM;

	// Resolve the HOST to an IP address
	error = getaddrinfo(HOST, PORT, &hints, &strmSvr);
	if (error) {
		fprintf(stderr, "Could not resolve the host address: %s\n", HOST);
		fprintf(stderr, "%s", gai_strerror(error));
		exit(1);
	}

	// Create a reliable, stream socket using TCP
	s = socket(strmSvr->ai_family, strmSvr->ai_socktype, strmSvr->ai_protocol);
	if (s == -1) {
		fprintf(stderr, "Could not create a socket.\n");
		fprintf(stderr, "%s\n", strerror(errno));
		exit(1);
	}

	// Connect to the socket
	error = connect(s, strmSvr->ai_addr, strmSvr->ai_addrlen);
	if (error == -1) {
		fprintf(stderr, "Could not connect to socket.\n");
		fprintf(stderr, "%s\n", strerror(errno));
		exit(1);
	}

	freeaddrinfo(strmSvr);
       
	// Send the query to the streamer server
	send_len = send(s, query, strlen(query), 0);
	if (send_len != strlen(query)) {
		fprintf(stderr, "Did not send the entire query.\n");
		fprintf(stderr, "Query len: %i, sent len: %i\n", (int) strlen(query), (int) send_len);
	}

	recv_len = recv(s, inbuf, INBUF_SIZE, 0);
	if (recv_len <= 0) {
		fprintf(stderr, "Receive failed.\n");
		exit(1);
	}

	printf("%s\n", inbuf);

	// Parse the returned JSON blob
	data = json_tokener_parse(inbuf);

	{
		json_object* profile;
		profile = json_object_object_get(data, "profile_id");
		printf("profile: %s\n", json_object_get_string(profile));

	}


	close(s);

	return 0;
}
