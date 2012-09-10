var socket;
var g;

var fields = ['cpu_usage', 'disk_usage', 'memory_usage', 'network_sent', 'network_receive'];


onload = function() {
	socket = io.connect('inductor.eecs.umich.edu:8080/stream');

	socket.on('connect', function (data) {
		var query = {hostname: 'nuclear.eecs.umich.edu'};
		socket.emit('query', query);
	});

	socket.on('data', function (data) {
		pdw = {};
		pd  = {};

		for (var i=0; i<fields.length; i++) {
			if (_.has(data, fields[i])) {
				pd[fields[i]] = [data['time']-14400000, data[fields[i]]];
			}
		}

		pdw = {name: data['hostname'], data:pd};
		g.addData(pdw);
		g.update();

	});


	g = $.grapher($("#nuclear_graph"));

}
