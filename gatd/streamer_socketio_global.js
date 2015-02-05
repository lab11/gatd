#!/usr/bin/env nodejs

/*
Stream data with socket.io
*/

var path = require('path');
var fs = require('fs');
var sio = require('socket.io');
var mc = require('mongodb').MongoClient;
var ini = require('simple-ini');

var config = new ini(function() {
                         return fs.readFileSync('/etc/gatd/gatd.config', 'utf-8');
			}, {'delimiter': ':',
				'comments': '#',
				'ignoreWhitespace': true});

var mongo_url = 'mongodb://'+config.blocks.mdb_username+':'
	+config.blocks.mdb_password+'@'+config.mongo.host+':'+config.mongo.port+
	'/'+config.mongo.database;



var namespace_connection = function (socket) {

	streamer_uuid = socket.nsp.name.substring(1, socket.nsp.name.length);

	socket.on('query', function (data) {

console.log('got query');
		mc.connect(mongo_url, {uri_decode_auth: true}, function (err, db) {
			if (err) {
				return console.dir(err);
			}else {

				var c = db.collection(streamer_uuid);

				var cursor_opts = {
					tailable: true,
					awaitdata: true,
					numberOfRetries: -1
				};

				var stream = c.find(data, cursor_opts).stream();

				stream.on('data', function (document) {
					socket.emit('packet', document);
				});

				stream.on('end', function() {
					db.close();
				});

			}

		});

	});
}



// Create the socket.io server
io = sio.listen(config.streamer_socketio.port)

// Allow for namespaces to be created dynamically
var socketio_connect_fn;
var transparently_create_namespace = function (name) {
	// Check if this namespace exists already
	if (!this.server.nsps[name]) {
		this.server.of(name, namespace_connection);
	}
	socketio_connect_fn.apply(this, arguments);
}

io.use(function(socket, next) {
	// Splice in our namespace function
	if (socketio_connect_fn !== socket.client.connect) {
		socketio_connect_fn = socket.client.connect;
	}
	socket.client.connect = transparently_create_namespace;

	return next();
});
