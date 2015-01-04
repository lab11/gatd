#!/usr/bin/env nodejs

var fs = require('fs');
// var app = require('http').createServer(handler)
var sio = require('socket.io');
var mc = require('mongodb').MongoClient;
var ini = require('simple-ini');

// function handler (req, res) {

// }


var config = new ini(function() {
						return fs.readFileSync('./gatd.config', 'utf-8');
			}, {'delimiter': ':',
				'comments': '#',
				'ignoreWhitespace': true});

var mongo_url = 'mongodb://'+config.blocks.mdb_username+':'
	+config.blocks.mdb_password+'@'+config.mongo.host+':'+config.mongo.port+
	'/'+config.mongo.database;

// console.log(mongo_url)

// mc.connect(mongo_url, function (err, db) {
// 	if (err) { return console.dir(err); }
// });





// mc.connect(mongo_url, {uri_decode_auth: true}, function (err, db) {
// 	if (err) {
// 		return console.dir(err);
// 	}else {


// 		// console.log(db);


// 		var c = db.collection('b0d2962d-659f-4e53-be24-255420e6b02f');

// 		var cursor_opts = {
// 			tailable: true,
// 			awaitdata: true,
// 			numberOfRetries: -1,
// 			// timeout: false
// 		};

// 		try {
// 			var stream = c.find({}, cursor_opts).stream();
// 		} catch (err) {
// 			console.log(err);
// 		}

// 		// console.log(stream);

// 		stream.on('data', function (document) {
// 			console.log(document);
// 		});

// 	//while (true) {
// 	// 	var m = function () {
// 	// 		stream.next(function (err, doc) {
// 	// 			if (doc) {
// 	// 				console.log(doc);
// 	// 			}
// 	// 			m();
// 	// 		});

// 	// 	}

// 	// 	m();
// 	// //}

// 		stream.on('end', function() {
// 			console.log('endeddddddd');
// 		      db.close();
// 		    });


// 	}
// });





var saved;

var oncon = function (socket) {

	streamer_uuid = socket.nsp.name.substring(1, socket.nsp.name.length);
	console.log('uuid '+streamer_uuid);

	mc.connect(mongo_url, {uri_decode_auth: true}, function (err, db) {
		if (err) {
			return console.dir(err);
		}else {

			console.log(streamer_uuid);

			// console.log(db);


			var c = db.collection(streamer_uuid);

			var cursor_opts = {
				tailable: true,
				awaitdata: true,
				numberOfRetries: -1
			};

			var stream = c.find({}, cursor_opts).stream();

			// console.log(stream);

			stream.on('data', function (document) {
				socket.emit('packet', document);
			});

			stream.on('end', function() {
			console.log('endeddddddd');
		      db.close();
		    });


			// db.collection(streamer_uuid, {strict:true}, function (err, c) {
			// db.collection(streamer_uuid, function (err, c) {
			// db.collection('b0d2962d-659f-4e53-be24-255420e6b02f', function (err, c) {
			// // db.collection('conf_profiles', {strict:true}, function (err, c) {
			// // db.collection('conf_profiles',  function (err, c) {
			// 	if (err) {
			// 		console.log('NO COLLECTION ARG');
			// 		console.log(err);
			// 	} else {

			// 		// c.find({}).toArray(function(err, items) {
			// 		// 	console.log(items);
			// 		// });

			// 		var cursor_opts = {
			// 			tailable: true,
			// 			awaitdata: true,
			// 			numberOfRetries: -1
			// 		};

			// 		var stream = collection.find({}, cursor_opts).stream();

			// 		stream.on('data', function (document) {
			// 			socket.emit('packet', document);
			// 		});
			// 	}
			// });

			// console.log(collection);

			// var result = db.system.namespaces.find({name: config.mongo.database+'.'+streamer_uuid});
			// console.log(result);
		}


	});

	console.log('HJDKJLOFHDS')



	// console.log(socket)
	//   socket.emit('news', { hello: 'world' });
 //  socket.on('my other event', function (data) {
 //    console.log(data);

}


var hack = function (name) {
	console.log('HAHA MY FUNC');
	console.log(name);

	if (!this.server.nsps[name]) {
		console.log('new namespace');
		this.server.of(name, oncon);
	} else {
		console.log('existing namespace');
	}

	saved.apply(this, arguments);
}



// app.listen(config.streamer_socketio.port);
io = sio.listen(config.streamer_socketio.port)

io.use(function(socket, next){
	// console.log(socket.client.connect);

	saved = socket.client.connect;
	socket.client.connect = hack;


	// console.log(socket);
	// console.log('use');
	return next();
  // if (socket.request.headers.cookie) return next();
  // next(new Error('Authentication error'));
});

io.of('/makethiswork').on('connection', function (socket) {
	// console.log(socket.nsp);
	console.log('connect');
  socket.emit('news', { hello: 'world' });
  socket.on('my other event', function (data) {
    console.log(data);
  });
});

