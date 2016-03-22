
var autocomp_jquery;
if(!autocomp_jquery)
{
	autocomp_jquery = jQuery;
}

var autocomp_single = function(fieldType, elementId, linkedToId)
{
	var element = autocomp_jquery('#' + elementId);
	var itemList = null;
	if(fieldType == "name")
	{
		itemList = _lang_name_list;
	}
	else
	{
		itemList = _lang_code_list;
	}
	element.autocomplete({
		select: function(event, ui)
		{
			var linkedValue = null;
			if(fieldType == "name")
			{
				linkedValue = _lang_name_to_code[ui.item.value];
			}
			else
			{
				linkedValue = _lang_code_to_name[ui.item.value];
			}
			var linkedElem = autocomp_jquery('input#' + linkedToId);
			if(!linkedElem.val())
			{
				linkedElem.val(linkedValue);
			}
		},
		source: itemList,
		minLength: 0
	}).data("autocomplete")._renderItem = function(ul, item){
		var itemText;
		if(fieldType == "name")
		{
			var langCode = _lang_name_to_code[item.label];
			itemText = langCode + " - " + item.label;
		}
		else
		{
			var langName = _lang_code_to_name[item.label];
			itemText = item.label + " - " + langName;
		}
		var a = autocomp_jquery('<li></li>')
		.data("item.autocomplete", item)
		.append(autocomp_jquery("<a></a>")["text"](itemText)).
		appendTo(ul);
	};
}

var autocomp_multi = function(fieldType, containerId, elementId, linkedElementId)
{
	var container = autocomp_jquery('#' + containerId);
	var element = container.find('#' + elementId);
	var itemList;
	if(fieldType == "name")
	{
		itemList = _lang_name_list;
	}
	else
	{
		itemList = _lang_code_list;
	}
	element.autocomplete({
		select: function(event, ui)
		{
			var linkedValue = null;
			if(fieldType == "name")
			{
				linkedValue = _lang_name_to_code[ui.item.value];
			}
			else
			{
				linkedValue = _lang_code_to_name[ui.item.value];
			}
			
			// find the index of this field
			var idParent = autocomp_jquery(this).parent();
			var idIndex = idParent.attr('id');
			idIndex = idIndex.replace(/container_[0-9]*_/, '');
			idIndex = parseInt(idIndex) + 1;
			
			// find the 'name' field with the same index
			var inp = autocomp_jquery('#' + linkedElementId);
			var ul = inp.parent().parent();
			var liCh = ul.find('li[id^=container]');
			var li = null;
			if(liCh.length >= idIndex)
			{
				li = ul.find('li[id]:nth-child(' + idIndex + ')');
			}
			else if(liCh.length == idIndex - 1)
			{
				var nameWidgetId = ul.attr('id');
				nameWidgetId = nameWidgetId.replace(/widget_/, '');
				nameWidgetId = parseInt(nameWidgetId);
				add_container(nameWidgetId);
				li = ul.find('li[id]:nth-child(' + idIndex + ')');
				
			}
			if(li)
			{
				var linkedInp = li.find('.input');
				if(!linkedInp.val())
				{
					linkedInp.val(linkedValue);
					autocomp_jquery(this).focus();
				}
			}
		},
		source: itemList,
		minLength: 0
	}).data("autocomplete")._renderItem = function(ul, item){
		var itemText;
		if(fieldType == "name")
		{
			var langCode = _lang_name_to_code[item.label];
			itemText = langCode + " - " + item.label;
		}
		else
		{
			var langName = _lang_code_to_name[item.label];
			itemText = item.label + " - " + langName;
		}
		var a = autocomp_jquery('<li></li>')
		.data("item.autocomplete", item)
		.append(autocomp_jquery("<a></a>")["text"](itemText)).
		appendTo(ul);
	};
}

var update_language_name = function(element)
{
	var val = element.val();
	var name = element.attr('name');
	var nameEl = autocomp_jquery('span[for=' + name + ']');
	var langVal = _lang_code_to_name[val];
	var textVal = '';
	if(langVal)
	{
		textVal = '(' + langVal + ')';
	}
	nameEl.text(textVal);
}

var autocomp_my_string = function(elem)
{
	var element = autocomp_jquery(elem);
	var itemList = _lang_code_list;
	element.autocomplete({
		select: function(event, ui)
		{
			element.val(ui.item.value);
			element.keyup();
		},
		source: itemList,
		minLength: 0
	}).data("autocomplete")._renderItem = function(ul, item){
		var itemText;
		var langName = _lang_code_to_name[item.label];
		itemText = item.label + " - " + langName;
		var a = autocomp_jquery('<li></li>')
		.data("item.autocomplete", item)
		.append(autocomp_jquery("<a></a>")["text"](itemText)).
		appendTo(ul);
	};
	element.keyup(function(){
		var a = autocomp_jquery(this);
		update_language_name(a);
	});
	element.change(function(){
		var a = autocomp_jquery(this);
		update_language_name(a);
	});
	update_language_name(element);
}

autocomp_jquery(document).ready(function(){
	$('input.lang_autocomplete').each(function(index){
		var elem = this;
		autocomp_my_string(elem);
	});
});
