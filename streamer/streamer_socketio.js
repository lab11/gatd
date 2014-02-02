var fs   = require('fs');
var net  = require('net');
var http = require('http');
var amqp = require('amqp');
var __   = require('underscore');
var qe   = require('query-engine');
var ini  = require('simple-ini');

var config = new ini(function() {
                       return fs.readFileSync('../config/gatd.config', 'utf-8');
                    }, {'delimiter': ':', 'comments': '#', 'ignoreWhitespace': true});

// Connect the socket.io socket to the correct port
var io = require('socket.io').listen(parseInt(config.socketio.port_node));

var clients = {};

// AMQP
var amqp_conn = amqp.createConnection({host: config.rabbitmq.host,
                                       port: parseInt(config.rabbitmq.port),
                                       login: config.rabbitmq.username,
                                       password: config.rabbitmq.password,
                                       authMechanism: 'AMQPLAIN'});
amqp_conn.on('ready', function () {
	var q = amqp_conn.queue('', {exclusive:true}, function () {
		q.bind(config.rabbitmq.xch_stream, '');
	});
	q.subscribe(function (message) {

		jmsg = JSON.parse(message.data);

		access = __.has(jmsg, 'public') && jmsg['public'] == true;

		for (var sid in __.keys(clients)) {
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
var stream = io.of(config.socketio.stream_prefix).on('connection', function (socket) {

	// Wait for configuration packet to begin
	socket.on('query', function (query, msg) {

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
