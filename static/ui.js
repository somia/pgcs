$(function() {
	$("#content").load("/dynamic", null, function() {
		$(".value").click(function() {
			alert($(this).find(".diff").text());
		});
	});
});
