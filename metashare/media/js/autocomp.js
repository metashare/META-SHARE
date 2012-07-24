
var autocomp_jquery;
if(!autocomp_jquery)
{
	autocomp_jquery = jQuery;
}

var autocomp_id = function(elementId, linkedToId)
{
	element = autocomp_jquery('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
			var name = _lang_alpha2_to_name[ui.item.value]
			autocomp_jquery('input#' + linkedToId).val(name);
		},
		source: _lang_alpha2_list
	});
}

var autocomp_name = function(elementId)
{
	element = autocomp_jquery('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
		},
		source: _lang_name_list
	});
}

