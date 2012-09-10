var net  = require('net');
var http = require('http');
var amqp = require('amqp');
var __   = require('underscore');
var jsIP = require('jsIP');
var qe   = require('query-engine');

RMQ_HOST = 'inductor.eecs.umich.edu';

// Connect the socket.io socket to port 8080
var io = require('socket.io').listen(8080);


var clients = {};


// AMQP
var amqp_conn = amqp.createConnection({host: RMQ_HOST});
amqp_conn.on('ready', function () {
	var q = amqp_conn.queue('streamer_queue', {durable:true, autoDelete:false});

	q.subscribe(function (message) {

		jmsg = JSON.parse(message.data);

		access = __.has(jmsg, 'public') && jmsg['public'] == true;


		//	console.log(jmsg);
		sockets = __.keys(clients);

		for (var sid in clients) {
			s = clients[sid]['socket'];

			if (__.has(clients[sid], 'qe')) {
				// If we don't have a querier skip this
				lqe = clients[sid]['qe'];

				// Check to see if this socket even wants this packet
				lqe._reset();
				lqe.add([jmsg]);
				result = lqe.toJSON();

				if (result.length == 0) {
					continue;
				}

				console.log('got item');

				// See if this socket has access
				if (!access) {
					// skip this loop if not
					if (__.has(clients[sid], 'auth')) {
						auth = clients[sid]['auth'];
						if (auth['profile_id'] != jmsg['profile_id']) {
							continue;
						}
					} else {
						continue;
					}
				}

				// If we get here the query matches and we have access
				s.emit('data', result[0]);


			}

		}

	});
});

// Main block for handling stream requests
var stream = io.of('/stream').on('connection', function (socket) {

	// Wait for configuration packet to begin
	socket.on('query', function (query, msg) {
		console.log(query);

		if (!__.has(clients, socket['id'])) {
			clients[socket['id']] = {};
		}

		// Create the querier for the connection
		q = qe.createLiveCollection().setQuery('q', query);


		clients[socket['id']]['qe']     = q;
		clients[socket['id']]['query']  = query;
		clients[socket['id']]['socket'] = socket;

	});

	socket.on('auth', function (auth, msg) {
		console.log(auth);

		if (!__.has(clients, socket['id'])) {
			clients[socket['id']] = {};
		}

		if (__.has(auth, 'profile_id')) {
			clients[socket['id']]['auth'] = auth;
		}

	});


	socket.on('disconnect', function () {
		console.log('removing socket');
		for (sid in clients) {
			if (sid == socket['id']) {
				delete clients[sid]['q'];
				delete clients[sid]['socket'];
				delete clients[sid];
				break;
			}
		}
	});

});

