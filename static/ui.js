$(function() {
	$("#content").load("/dynamic", null, function() {
		$("tr.value").click(function() {
			alert($(this).find("div.value").text());
		});
	});
});
