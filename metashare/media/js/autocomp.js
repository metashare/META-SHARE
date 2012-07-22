

var autocomp_id = function(element, linkedToId)
{
	element.autocomplete({
		select: function(event, ui)
		{
			var name = _lang_alpha2_to_name[ui.item.value]
			$('input#' + linkedToId).val(name);
		},
		source: _lang_alpha2_list
	});
}

var autocomp_name = function(element)
{
	element.autocomplete({
		select: function(event, ui)
		{
		},
		source: _lang_name_list
	});
}

