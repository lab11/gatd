"use strict";

var jsp;

/*
options: {
	source_group: [a,b,c],
	target_group: [a,b,c]
}
*/
function new_block (name, options) {
	var colors = {
		'a': '#5696BC',
		'b': '#E04836',
		'c': '#F39D41'
	}

	var new_block = $('<div>', {class: 'w ui-draggable'})
	                 .text(name);
	var new_source = $('<div>', {class: 'source-group'});
	var new_target = $('<div>', {class: 'target-group'});

	$("#gatd-editor").append(new_block);


	jsp.draggable($(new_block));

	if ('source_group' in options && options['source_group'] != null) {
		new_source.addClass('group-'+options['source_group']);
		$(new_block).append(new_source);

		jsp.makeSource($(new_block), {
			filter: '.source-group', // make the block the source but only work from the little square
			anchor: "AutoDefault",   // use the best anchor, but only in the middle of each side
			connector:[ "Flowchart", { cornerRadius:5 } ], // make the connectors straight lines with 90 degree bends
			connectorStyle:{ strokeStyle: colors[options['source_group']],
			                 lineWidth: 2,
			                 outlineColor: "transparent",
			                 outlineWidth: 4
			               },
			scope: options['source_group'],
			maxConnections: 5,
			onMaxConnections: function(info, e) {
				alert("Maximum connections (" + info.maxConnections + ") reached");
			}
		});
	}

	if ('target_group' in options && options['target_group'] != null) {
		new_target.addClass('group-'+options['target_group']);
		$(new_block).append(new_target);

		jsp.makeTarget($(new_block), {
			dropOptions: {hoverClass:"dragHover"},
			anchor: "AutoDefault",
			allowLoopback: false,
			scope: options['target_group']
		});
	}

	
	

	// if (input) {
	// 	$(new_block).append(input_type);
	// }


	// jsp.draggable($(new_block));


	// jsp.makeSource($(new_block), {
	// 	filter: '.source-group', // make the block the source but only work from the little square
	// 	anchor: "AutoDefault",   // use the best anchor, but only in the middle of each side
	// 	connector:[ "Flowchart", { cornerRadius:5 } ], // make the connectors straight lines with 90 degree bends
	// 	connectorStyle:{ strokeStyle: "#5c96bc",
	// 	                 lineWidth: 2,
	// 	                 outlineColor: "transparent",
	// 	                 outlineWidth: 4
	// 	               },
	// 	maxConnections: 5,
	// 	onMaxConnections: function(info, e) {
	// 		alert("Maximum connections (" + info.maxConnections + ") reached");
	// 	}
	// });


	// jsp.makeTarget($(new_block), {
	// 	dropOptions:{ hoverClass:"dragHover" },
	// 	anchor:"AutoDefault",
	// 	allowLoopback:false
	// });

}


jsPlumb.ready(function() {

	// setup some defaults for jsPlumb.
	jsp = jsPlumb.getInstance({
		Endpoint:           ["Dot", {radius:2}],
		HoverPaintStyle:    {strokeStyle:"#1e8151", lineWidth:2 },
		ConnectionOverlays: [
		                      ["Arrow", {
		                                  location: 1,
		                                  id:       "arrow",
		                                  length:   10,
		                                  foldback: 1
		                                }],
		                      // ["Label", {
		                      //             label:    "FOO",
		                      //             id:       "label",
		                      //             cssClass: "aLabel" }]
		                    ],
		Container:          "gatd-editor"
	});

	new_block('UDP Receiver (IPv6)', {'source_group':'a'});
	new_block('Formatter', {'source_group': 'b',
		                    'target_group': 'a'});
	new_block('Processor', {'source_group': 'b',
		                    'target_group': 'a'});
	new_block('Mongo DB', {'source_group': 'c',
                           'target_group': 'b'})
});