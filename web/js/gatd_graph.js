
// Map ccid_mac to hex color string
var node_mapping = {};
var number_nodes = 0;

var key_map = {};

var series = 'all';

function add_to_graph(graph, uid, x, y, color) {
	pd = {}
	pd[uid] = [x, y]
	pdw = {name: '',
	       data:pd,
	       color:color,
	       lines:{show:true},
	       points:{show:true,
	               radius:4,
	               fill:true,
	               fillColor:color},
	   };
	graph.addData(pdw);
	graph.update(series);
}


function x_format(val, axis) {
	d = new Date(val);

	sec = d.getSeconds();
	if (sec != 0 && sec != 30) {
		return '';
	}

	var leftPad = function(n, pad) {
		n = "" + n;
		pad = "" + (pad == null ? "0" : pad);
		return n.length == 1 ? pad + n : n;
	};

	var hours = d.getHours();
	var isAM = hours < 12;

	if (hours > 12) {
		hours12 = hours - 12;
	} else if (hours == 0) {
		hours12 = 12;
	} else {
		hours12 = hours;
	}

    return hours12 + ":" + leftPad(d.getMinutes()) + ":" +
           leftPad(sec) + " " + ((isAM)?"AM":"PM");
}

function get_color (uid) {
	if (!(uid in node_mapping)) {
		node_mapping[uid] = get_random_color();
	}
	return node_mapping[uid];
}

function get_random_color() {
	var letters = '0123456789ABCDEF'.split('');
	var color = '#';
	for (var i = 0; i < 6; i++ ) {
		color += letters[Math.round(Math.random() * 15)];
	}
	return color;
}

function add_to_key (graph, uid, desc, loc, color) {
	if (!(uid in key_map)) {
		key_map[uid] = {'description': desc,
		                'location': loc,
		                'color': color};
		loc = loc.replace(/[\|]+/g, ", ").replace("|", ", ");
		uid_stripped = uid.replace(/[^a-zA-Z0-9]/g, '');
		$("#key_table").append('<tr id="'+uid_stripped+'" style="color:'
								+ color + '"><td>'+number_nodes+'</td><td>'
								+uid+'</td><td>'+desc+'</td><td>'
								+loc+'</td></tr>');
		$("tr#"+uid_stripped).click(function() {
			series = uid;
			graph.update(series);
		});
		number_nodes++;
	}
}

