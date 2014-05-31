

(function ($) {
	var Grapher = function (placeholder, options) {
		var
			data       = {},
			meta       = {},
			max_x      = 0,
			width      = 0,
			num_lines  = 0,
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

					data[key_name].push(s[si]);

					if (s[si][0] > max_x) {
						max_x = s[si][0];
					}

					meta[key_name] = {color: d[group_i]['color'],
					                  yaxis: d[group_i]['yaxis'],
					                  lines: d[group_i]['lines'],
					                  points: d[group_i]['points'],
					                 }
				}
			}

		}

		function removeSeries (name) {
			for (key in data) {
				if (key.indexOf(name) == 0) {
					delete data[key];
				}
			}
		}

		function update (series) {

			// Make sure all data points fit within the width of the
			// graph.
			// This method requires the x axis values to be in
			// increasing order.

			var min = max_x - width;
			var i;
			for (key in data) {
				for(i=0; i<data[key].length; i++) {
					if (data[key][i][0] >= min) {
						break;
					}
				}
				if (i > 0) {
					if (i >= data[key].length) {
						// Remove all points from this series
						delete data[key];
					} else {
						// Remove all points that are before the beginning of
						// x axis
						data[key] = data[key].slice(i);
					}
				}
			}


			commitData(series);
			plot.setupGrid();
			plot.draw();
		}

		function commitData (series) {
			if (typeof(series) === 'undefined') series = 'all';
			graph_data = [];

			for (x in data) {
				if (series == 'all' || x == series) {
					s = [];
					for (i in data[x]) {
						if (_.isArray(data[x][i])) {
							s.push(data[x][i]);
						} else {
							s.push([parseInt(i), data[x][i], 10]);
						}
					}
					t = {'label': x,
					     'data': s,
					     'color': meta[x]['color'],
					     'yaxis': meta[x]['yaxis'],
					     'lines': meta[x]['lines'],
					     'points': meta[x]['points'],
					 };
					graph_data.push(t);
				}
			}

			plot.setData(graph_data);
		}

		width = options['xaxis']['width'];

		plot = $.plot(placeholder, [[0,0]], options);

		if (options['yaxis']['label']) {
			var yaxisLabel = $("<div class='axisLabel yaxisLabel'></div>")
				.text(options['yaxis']['label'])
				.appendTo(placeholder);
			yaxisLabel.css("margin-top", yaxisLabel.width() / 2 - 20);
		}
	/*	if (options['yaxes'][1]['label']) {
			var y2axisLabel = $("<div class='axisLabel y2axisLabel'></div>")
				.text(options['yaxes'][1]['label'])
				.appendTo(placeholder);
			//y2axisLabel.css("margin-top", y2axisLabel.width() / 2 - 50);
		}*/

	}

	$.grapher = function (placeholder) {
		var user_opts = arguments[1];

		var label_format = function (label, b) {
			// Capitalize and remove underscores
			label = label.replace('_', ' ');
			return label.replace(/\w\S*/g, function(txt) {
				return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
			});
		}

		function xformatter(val, axis) {
		    return val.toFixed(axis.tickDecimals);
		}

		var options = {
			series: {shadowSize: 0},
			xaxis: {show:true, width:120000, mode: "time", timeformat: "%I:%M:%S %P"},
			yaxis: {min:0},
			//yaxes: user_opts['yaxes'],
			legend: {show:false, labelFormatter: label_format},
			colors: user_opts['colors'],

		};

		$.extend(options, user_opts);


		var g = new Grapher($(placeholder), options);

		return g;
	}

})(jQuery)
