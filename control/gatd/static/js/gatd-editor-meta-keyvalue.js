$(document).ready(function() {

	$("#meta-key-value-new").click(function () {
		console.log('new')
		var r = Math.floor((Math.random() * 100000) + 1);
		var row = $("#meta-key-value-row").clone().attr('id', r);
		row.removeAttr('style');
		row.find('input').each(function () {
			var name = $(this).attr('name') + '-' + r;
			if (name.indexOf('addit') > -1) {
				name += '-0';
			}
			$(this).attr('name', name);
		});
		$("#meta-key-value-table tbody").prepend(row);
	});

});