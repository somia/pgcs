$(function() {
	$("#content").load("/dynamic", null, function() {
		$("tr.diff").click(function() {
			alert($(this).find("div.value").text());
		});
	});
});
