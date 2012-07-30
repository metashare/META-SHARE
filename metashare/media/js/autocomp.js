
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
		source: _lang_alpha2_list,
		minLength: 0
	}).data("autocomplete")._renderItem = function(ul, item){
		var langName = _lang_alpha2_to_name[item.label];
		var a = autocomp_jquery('<li></li>')
			.data("item.autocomplete", item)
			.append(autocomp_jquery("<a></a>")["text"](item.label + " - " + langName)).
			appendTo(ul);
	};
}

var autocomp_name = function(elementId)
{
	element = autocomp_jquery('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
		},
		source: _lang_name_list,
		minLength: 0
	});
}

