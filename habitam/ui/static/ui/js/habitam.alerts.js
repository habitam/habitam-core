function cookieId(el) {
	return 'habitam-alert-hide:' + el.attr('id');
}

$(function() {
	$('.habitam-alert').each(function() {
		if ($.cookie(cookieId($(this))) == 1)
			return;
		$(this).alert();
		$(this).show();
	});

	$('.habitam-alert-close').click(function() {
		$.cookie(cookieId($(this).parent()), 1);
		$(this).parent().alert('close');
	});
});