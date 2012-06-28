
function showFieldHelp(obj)
{
	var $ = django.jQuery;
	var b = $(obj);
	var a = $(obj).children('.help').get(0);
	var pos = $(a).position();
	var top = 15;
	var left = 0;
	$(a).css('clear', 'both');
	$(a).css({top: top, left: left, padding: 0, margin: 0});
	$(a).show();
}

function hideFieldHelp(obj)
{
	var $ = django.jQuery;
	var a = $(obj);
	$(obj).children('.help').hide();
}
