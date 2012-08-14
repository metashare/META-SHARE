
var autocomp_jquery;
if(!autocomp_jquery)
{
	autocomp_jquery = jQuery;
}

var autocomp_id = function(elementId, linkedToId)
{
	var element = autocomp_jquery('#' + elementId);
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
	var element = autocomp_jquery('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
		},
		source: _lang_name_list,
		minLength: 0
	});
}

var autocomp_m_id = function(containerId, elementId, linkedElementId)
{
	var container = autocomp_jquery('#' + containerId);
	var element = container.find('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
			var name = _lang_alpha2_to_name[ui.item.value];
			
			// find the index of this field
			var idParent = autocomp_jquery(this).parent();
			var idIndex = idParent.attr('id');
			idIndex = idIndex.replace(/container_[0-9]*_/, '');
			idIndex = parseInt(idIndex) + 1;
			
			// find the 'name' field with the same index
			var inp = autocomp_jquery('#' + linkedElementId);
			var ul = inp.parent().parent();
			var li = ul.find('li[id]:nth-child(' + idIndex + ')');
			if(li.length == 0)
			{
				var nameWidgetId = ul.attr('id');
				nameWidgetId = nameWidgetId.replace(/widget_/, '');
				nameWidgetId = parseInt(nameWidgetId);
				add_container(nameWidgetId);
				li = ul.find('li[id]:nth-child(' + idIndex + ')');
			}
			var linkedInp = li.find('.input');
			linkedInp.val(name);
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

var autocomp_m_name = function(containerId, elementId)
{
	var container = autocomp_jquery('#' + containerId);
	var element = container.find('#' + elementId);
	element.autocomplete({
		select: function(event, ui)
		{
		},
		source: _lang_name_list,
		minLength: 0
	});
}

