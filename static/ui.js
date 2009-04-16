$(function() {
	$("#content").load("/dynamic", null, function() {
		$(".expander").click(function() {
			$(this).siblings(".children").show();
			//$(this).siblings(".columns").hide();
			$(this).hide();
		});

		$(".value").click(function() {
			alert($(this).find(".diff").text());
		});
	});
});
