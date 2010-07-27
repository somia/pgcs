$(function() {
	$(".expander").click(function() {
		if ($(this).text() == "+") {
			$(this).siblings(".children").show();
			$(this).text("-");
		} else {
			$(this).siblings(".children").hide();
			$(this).text("+");
		}
	});

	$(".value").click(function() {
		alert($(this).find(".diff").text());
	});
});
