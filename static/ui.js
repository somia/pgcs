$(function() {
	$("#content").load("/dynamic", null, function() {
		$(".expander").click(function() {
			if ($(this).text() == "+") {
				$(this).siblings(".children").show();
				$(this).siblings(".columns").hide();
				$(this).text("-");
			} else {
				$(this).siblings(".children").hide();
				$(this).siblings(".columns").show();
				$(this).text("+");
			}
		});

		$(".value").click(function() {
			alert($(this).find(".diff").text());
		});
	});
});
