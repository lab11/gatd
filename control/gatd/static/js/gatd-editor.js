"use strict";

var jsp;


function new_block (uuid) {
	var colors = {
		'a': '#5696BC',
		'b': '#E04836',
		'c': '#F39D41'
	}

	var new_block = $('#'+uuid);

	// Initialize the popup
	// $('#block_'+uuid+'_popup').popup({
	// 	positionTo: "origin"
	// });
	// $('#block_'+uuid+'_popup').css('display', 'block');

	//  Make the popup appear on dbl click
	$('#'+uuid).dblclick(function () {

		$(this).popover('show');


		// var position = $(this).position();
		// $('#block_'+uuid+'_popup').popup('open', {
		// 	x: position.left,
		// 	y: position.top
		// });
	});

	// // Initialize tooltips
	// $('#block_'+uuid+'_popup .tooltipster').tooltipster({
	// 	theme: 'tooltipster-light',
	// });

	// Make the block dragable
	jsp.draggable(uuid);

	var source_group = new_block.attr('data-source-group');
	var target_group = new_block.attr('data-target-group');

	// Setup arrow properties
	if (source_group) {
		jsp.makeSource($(new_block), {
			filter: '.source-group', // make the block the source but only work from the little square
			anchor: "AutoDefault",   // use the best anchor, but only in the middle of each side
			connector:[ "Flowchart", { cornerRadius:5 } ], // make the connectors straight lines with 90 degree bends
			connectorStyle:{ strokeStyle: colors[source_group],
			                 lineWidth: 2,
			                 outlineColor: "transparent",
			                 outlineWidth: 4,
			                 dashstyle: "0"
			               },
			connectorHoverStyle:{ strokeStyle: colors[source_group],
			                 lineWidth: 2,
			                 outlineColor: "transparent",
			                 outlineWidth: 4,
			                 dashstyle: "2 2"
			               },
			scope: source_group,
			maxConnections: 5,
			onMaxConnections: function(info, e) {
				alert("Maximum connections (" + info.maxConnections + ") reached");
			}
		});
	}

	if (target_group) {
		jsp.makeTarget($(new_block), {
			dropOptions: {hoverClass:"dragHover"},
			anchor: "AutoDefault",
			allowLoopback: false,
			scope: target_group
		});
	}

}

function save_profile () {
	var blocks = [];
	var connections = [];

	var connection_ids = {};

	// Add all blocks
	$('.block').each(function () {
		//console.log($(this));

		var block = Object();
		block.uuid = $(this).attr('id');
		block.type = $(this).attr('data-type');

		var pos = $(this).position()
		block.top = pos.top;
		block.left = pos.left;

		var popup = $('#block_'+block.uuid+'_popup');

		// Save all of the parameters
		popup.find('.parameter').each(function () {
			var key = $(this).attr('data-key');
			var val = $(this).attr('data-value');
			block[key] = val;
		});

		// Get the value of each setting
		popup.find('.setting').each(function () {
			var key = $(this).attr('data-key');
			var val = $(this).val();
			block[key] = val;
		});

		blocks.push(block);
	});

	// Add all unique connections
	var duplicates = {};
	var existing_connections = jsp.getAllConnections();
	for (var i=0; i<existing_connections.length; i++) {
		var src = existing_connections[i].sourceId;
		var tar = existing_connections[i].targetId;

		var dupe_check = src+tar;
		if (dupe_check in duplicates) {
			continue;
		}
		duplicates[dupe_check] = true;

		var connection = Object();
		connection.source_uuid = src;
		connection.target_uuid = tar;

		connections.push(connection);

		// Keep track of all blocks that are connected so we can get rid of
		// floating blocks that aren't connected to anything.
		connection_ids[src] = true;
		connection_ids[tar] = true;
	}

	// Remove any blocks that aren't connected to anything.
	var blocks_len = blocks.length;
	while (blocks_len--) {
		if (!(blocks[blocks_len].uuid in connection_ids)) {
			blocks.splice(blocks_len, 1);
		}
	}

	var profile = Object();

	profile.uuid = $('#gatd-editor').attr('data-profile-uuid');
	profile.name = $('#profile-name').text();
	profile.blocks = blocks;
	profile.connections = connections;

	return profile;
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
    		["Label", {
    			label: 'X',
				cssClass: 'aLabel',
				id:"delete"
			}]
		                    ],
		Container:          "gatd-editor"
	});

	// When a connection is created, update the attributes of the overlay
	// label so we can associate a click on it to the correct connection.
	jsp.bind("connection", function(info) {
		 $(info.connection.getOverlay("delete").canvas)
		  .attr('data-tar', info.connection.targetId)
		  .attr('data-src', info.connection.sourceId)
		  .attr('data-scope', info.connection.scope);
	});

	// Delete connection when the label is clicked
	$('#gatd-editor').on('click', '.aLabel', function () {
		var src = $(this).attr('data-src');
		var tar = $(this).attr('data-tar');
		var scope = $(this).attr('data-scope');

		$.each(jsp.getConnections({scope:scope, source:src, target:tar}), function(i,v) {
			jsp.detach(v);
		});
	});

	// Iterate through all saved blocks
	$('.block').each(function () {
		new_block($(this).attr('id'));
	});

	// Connect blocks
	$('.connection').each(function () {
		var src = $(this).attr('data-src');
		var tar = $(this).attr('data-tar');
		jsp.connect({source:src, target:tar});
	});

	// Make profile name editable
	$('#profile-name').editable();

	// Setup save popups
	// $('#popup-editor-save').popup({
	// 	overlayTheme: "b"
	// });
	// $('#popup-editor-save').css('display', 'block');

	$(".gatd-editor-button").click(function () {
		var block_type = $(this).attr('data-block');
		$.ajax('/editor/block/'+block_type, {'dataType': 'json'})
		.done(function (j) {
			if (j.status != 'success') {
				console.log('Error occurred getting block.');
				return;
			}
			$("#gatd-editor").append(j.html);
			new_block(j.block.uuid);
		});
	});

	$('#gatd-editor-save').click(function () {
		var data = save_profile();

		$.ajax({
			type: 'POST',
			url: '/editor/save',
			data: JSON.stringify(data),
			contentType: 'application/json',
			success: function () {
				$('#modal-profile-save').modal('hide');
			}
		})
		.fail(function () {
			console.log('fail');
		});
	});

	$('#gatd-editor-upload').click(function () {
		var data = save_profile();

		$.ajax({
			type: 'POST',
			url: '/editor/saveupload',
			data: JSON.stringify(data),
			contentType: 'application/json',
			success: function (data) {
				console.log(data);
				$('#modal-profile-upload').modal('hide');
			}
		})
		.fail(function () {
			console.log('fail');
		});
	});


	$('.block').each(function() {
		var pop = $(this).find('.block_popup');
		$(this).popover({
			content: pop.find('.block_popup_content').html(),
			html: true,
			placement: 'auto',
			trigger: 'manual',
			title: pop.find('.block_popup_title').html(),
		});
		$(this).find('.block_popup').remove();
	});

	$('#gatd-editor').on('click', '.popover .close', function () {
		var popid = $(this).attr('data-popover-id');
		$('#'+popid).popover('hide');
	});

		// Initialize tooltips
	$('.tooltipster').tooltipster({
		theme: 'tooltipster-light',
	});

});