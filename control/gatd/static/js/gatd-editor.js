"use strict";

var jsp;

/*
options: {
	source_group: [a,b,c],
	target_group: [a,b,c]
}
*/
function new_block (name, block_uuid, html, options) {
	var colors = {
		'a': '#5696BC',
		'b': '#E04836',
		'c': '#F39D41'
	}

	var new_block = $('<div>', {class: 'w ui-draggable'})
	                 .text(name)
	                 .attr('data-blockid', block_uuid);
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

	$(new_block).append(html);

	// Initialize the popup
	$('#block_'+block_uuid+'_popup').popup({
		positionTo: "origin"
	});

	$(new_block).dblclick(function () {
		var position = $(this).position();
		$('#block_'+block_uuid+'_popup').popup('open', {
			x: position.left,
			y: position.top
		});
	});

}

function save_profile () {
	var blocks = [];

	// {
	// 	'block_id': 
	// 	'top': 
	// 	'left':
	// 	'settings': [
	// 	],
	// 	'parameters': [
	// 	]
	// }
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

	$(".gatd-editor-button").click(function () {
		var block_type = $(this).attr('data-block');
		$.ajax('/editor/block/'+block_type, {'dataType': 'json'})
		.done(function (j) {
			if (j.status != 'success') {
				console.log('Error occurred getting block.');
				return;
			}
			var opts = {'source_group': j.block.source_group,
			            'target_group': j.block.target_group}
			new_block(j.block.name, j.block.uuid, j.html, opts);
		});
	});


	// new_block('UDP Receiver (IPv6)', {'source_group':'a'});
	// new_block('Formatter', {'source_group': 'b',
	// 	                    'target_group': 'a'});
	// new_block('Processor', {'source_group': 'b',
	// 	                    'target_group': 'a'});
	// new_block('Mongo DB', {'source_group': 'c',
 //                           'target_group': 'b'})
});