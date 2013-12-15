var net  = require('net');
var http = require('http');
//var amqp = require('amqp');
var __   = require('underscore');
//var jsIP = require('jsIP');
//var qe   = require('query-engine');
var fs   = fs = require('fs');

RMQ_HOST = 'inductor.eecs.umich.edu';

// Connect the socket.io socket to port 8080
var io = require('socket.io').listen(8080);


var clients = {};

var monjolo_packets_stream = fs.createReadStream('cc2520_pkts');
var wattsup_packets_stream = fs.createReadStream('wattsup');

json_recon = ''
json_recon_wup = ''

monjolo_packets_stream.on('data', function(chunk) {
	try {
		aa=JSON.parse(chunk);
	} catch (e) {
		if (String(chunk).charAt(0) == '{') {
			json_recon = chunk;
		} else {
			json_recon += chunk;
			try {
				aa=JSON.parse(json_recon);
			} catch (f) {
				return
			}
		}
	}

	sockets = __.keys(clients);

	for (var sid in clients) {
		s = clients[sid]['socket'];
		// If we get here the query matches and we have access
		s.emit('data', aa);
	}

})

wattsup_packets_stream.on('data', function(chunk) {
	console.log(chunk);
	try {
		aa=JSON.parse(chunk);
	} catch (e) {
		if (String(chunk).charAt(0) == '{') {
			json_recon_wup = chunk;
		} else {
			json_recon_wup += chunk;
			try {
				aa=JSON.parse(json_recon_wup);
			} catch (f) {
				return
			}
		}
	}

	sockets = __.keys(clients);

	for (var sid in clients) {
		s = clients[sid]['socket'];
		// If we get here the query matches and we have access
		s.emit('data', aa);
	}

})


/*
// AMQP
var amqp_conn = amqp.createConnection({host: RMQ_HOST});
amqp_conn.on('ready', function () {
	var q = amqp_conn.queue('', {exclusive:true}, function () {
		q.bind('streamer_exchange', '');
	});
	q.subscribe(function (message) {

		jmsg = JSON.parse(message.data);

		access = __.has(jmsg, 'public') && jmsg['public'] == true;
console.log(jmsg);

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
*/

// Main block for handling stream requests
var stream = io.of('/stream').on('connection', function (socket) {

	// Wait for configuration packet to begin
	socket.on('query', function (query, msg) {
		console.log(query);

		if (!__.has(clients, socket['id'])) {
			clients[socket['id']] = {};
		}

		// Create the querier for the connection
		clients[socket['id']]['socket'] = socket;

	});


	socket.on('disconnect', function () {
		for (sid in clients) {
			if (sid == socket['id']) {
				delete clients[sid]['socket'];
				delete clients[sid];
				break;
			}
		}
	});

});

