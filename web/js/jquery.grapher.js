

(function ($) {
	var Grapher = function (placeholder, options) {
		var
			data       = {},
			num_lines  = 0,
			num_points = 300,
			plot,
			graph = this;

		graph.addData = addData;
		graph.update = update;
		graph.removeSeries = removeSeries;


		function addData (d) {
			// Check to see if d is just a dict of data values
			// Or if it is a list of name:, data: keys

			// Need data to be a list of {name:, data:{}}


			if (_.isArray(d)) {
				// we're good
			} else if (_.has(d, 'name') && _.has(d, 'data')) {
				// only have 1 element
				// just need to put it in a list
				d = [d];

			} else {
				d = [{'name': '', 'data': d}]
			}

			for (group_i in d) {
				name = d[group_i]['name'];
				s    = d[group_i]['data']; // series

				if (typeof s == 'number' || _.isArray(s)) {
					s = {'': s};
				}

				for (si in s) {
					key_name = name=='' ? si : name + ' - ' + si;
					if (!_.isArray(data[key_name])) {
						data[key_name] = [];
					}
					if (data[key_name].length == num_points) {
						// remove the first element
						data[key_name] = data[key_name].slice(1);
					}

					data[key_name].push(s[si]);
				}

			}

/*
			// d should be an associative array
			for (xi in d) {
				d[xi] = _.isArray(d[xi]) ? d[xi].slice() : [d[xi]];

				for (j in d[xi]) {
					if (_.isArray(data[xi])) {
						if (data[xi].length == num_points) {
							// remove the first element
							data[xi] = data[xi].slice(1);
						}
						data[xi].push(d[xi][j]);
					} else {
						data[xi] = [d[xi][j]];
					}
				}

			}
			*/

		}

		function removeSeries (name) {
			for (key in data) {
				if (key.indexOf(name) == 0) {
					delete data[key];
				}
			}
		}

		function update () {
			commitData();
			plot.setupGrid();
			plot.draw();
		}

		function commitData () {
			graph_data = [];

			for (x in data) {
				s = [];
				for (i in data[x]) {
					if (_.isArray(data[x][i])) {
						s.push(data[x][i]);
					} else {
						s.push([parseInt(i), data[x][i]]);
					}
				}
				t = {'label': x, 'data': s};
				graph_data.push(t);
			}

			plot.setData(graph_data);
	//		console.log(graph_data);
		}

		plot = $.plot(placeholder, [[0,0]], options);
	}

	$.grapher = function (placeholder) {
		var options = arguments[1];
		var graph_key = (_.has(options, 'graph_key')) ? options['graph_key'] : null;

		var label_format = function (label, b) {
			// Capitalize and remove underscores
			label = label.replace('_', ' ');
			return label.replace(/\w\S*/g, function(txt) {
				return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
			});
		}

		var options = {
			series: {shadowSize: 0},
		//	yaxis: {min:0, max:100},
			xaxis: {show:true, width:900000, mode: "time", timeformat: "%h:%M:%S"},
			legend: {show:true, labelFormatter: label_format, container: graph_key}

		};



		var g = new Grapher($(placeholder), options);

		return g;
	}

})(jQuery)
