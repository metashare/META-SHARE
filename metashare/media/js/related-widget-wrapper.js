/*
 * From http://djangosnippets.org/snippets/2564/
 */

function dismissEditRelatedPopup(win, objId, newRepr) {
	objId = html_unescape(objId);
	newRepr = html_unescape(newRepr);
	newRepr = newRepr.replace(/</g, '&lt;');
	newRepr = newRepr.replace(/>/g, '&gt;');
	var name = windowname_to_id(win.name).replace(/^edit_/, '');
	var elem = document.getElementById(name);
	if (elem && elem.nodeName == 'SELECT') {
		var opts = elem.options,
			l = opts.length;
		for (var i = 0; i < l; i++) {
			if (opts[i] && opts[i].value == objId) {
				opts[i].innerHTML = newRepr;
			}
		}
	}
	
	if( $("a#edit_"+elem.id).text().indexOf("General Info") !=-1 || $("a#edit_"+elem.id).text().indexOf("Tool") !=-1){
		$("input.edit_"+elem.id).attr('value', objId);
		$("input.edit_"+elem.id).trigger('change');		
	}
	else
	{
		$("#"+elem.id).trigger('change', newRepr);
	}
	win.close();
};

function saveAndContinuePopup(win, newId, newRepr, url) {
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem) {
        if (elem.nodeName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elem.nodeName == 'INPUT') {
            if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
                elem.value += ',' + newId;
            } else {
                elem.value = newId;
            }
        }
    } else {
        var toId = name + "_to";
        elem = document.getElementById(toId);
        var o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
	win.location.replace(url);
};

if (!saveAndContinuePopup.original) {
	var originalsaveAndContinuePopup = saveAndContinuePopup;
	saveAndContinuePopup = function(win, newId, newRepr, url) {
		originalsaveAndContinuePopup(win, newId, newRepr, url);
		newId = html_unescape(newId);
		newRepr = html_unescape(newRepr);
		var id = windowname_to_id(win.name);
		$('#' + id).trigger('change', newRepr);
	};
	saveAndContinuePopup.original = originalsaveAndContinuePopup;
}

if (!dismissAddAnotherPopup.original) {
	var originalDismissAddAnotherPopup = dismissAddAnotherPopup;
	dismissAddAnotherPopup = function(win, newId, newRepr) {
		originalDismissAddAnotherPopup(win, newId, newRepr);
		newId = html_unescape(newId);
		newRepr = html_unescape(newRepr);
		var id = windowname_to_id(win.name);
		$('#' + id).trigger('change', newRepr);
	};
	dismissAddAnotherPopup.original = originalDismissAddAnotherPopup;
}

function dismissDeleteRelatedPopup(win) {
	var name = windowname_to_id(win.name).replace(/^delete_/, '');
	win.close();
	var elem = document.getElementById(name);
	elem.value = '';
	$('#' + name).trigger('change', '__delete__');
}

django.jQuery(document).ready(function() {
  
  var $ = $ || jQuery || django.jQuery;
  var changeSelector = '.related-widget-wrapper-change-link';
  var addSelector = '.related-widget-wrapper-add-link';
  var deleteSelector = '.related-widget-wrapper-delete-link';
  var hrefTemplateAttr = 'data-href-template';
  
  $('.related-widget-wrapper').live('change', function(event, newRepr){
  	var changeLink = $(this).nextAll(changeSelector);
  	var addLink = $(this).nextAll(addSelector);
  	var deleteLink = $(this).nextAll(deleteSelector);
  	if (this.value) {
  		var val = this.value;
  		changeLink.each(function(){
  			var elm = $(this);
  			elm.attr('href', interpolate(elm.attr(hrefTemplateAttr), [val]));
  			// Show the change-link for the new/edited related object.
  			elm.show();
  		});
  		deleteLink.each(function(){
  			var elm = $(this);
  			elm.attr('href', interpolate(elm.attr(hrefTemplateAttr), [val]));
  			// Show the change-link for the new/edited related object.
  			elm.show();
  		});
  		addLink.hide();
  	} else { // no value
  		changeLink.removeAttr('href').hide();
  		deleteLink.removeAttr('href').hide();
  		addLink.show();
  	}
  	if(newRepr)
  	{
  		var elem = $(this);
  		if(elem)
  		{
  			var content = $(elem).parent().children('span.related-widget-wrapper-content').get(0);
  			if(content)
  			{
  				if(newRepr == '__delete__')
  				{
  	  				var jqContent = $(content);
  	  				jqContent.text('');
  				}
  				else
  				{
  	  				var jqContent = $(content);
  	  				jqContent.text(newRepr);
  				}
  			}
  		}
  	}
  });

  // Hide change-link for related widgets not containing an object id.
  $('.related-widget-wrapper').each(function(index) {
	  var changeLink = $(this).nextAll(changeSelector);
	  var addLink = $(this).nextAll(addSelector);
	  var deleteLink = $(this).nextAll(deleteSelector);
	  if ($(this).val()) {
		  changeLink.show();
		  addLink.hide();
		  deleteLink.show();
	  } else {
		  changeLink.hide();
		  addLink.show();
		  deleteLink.hide();
	  }
  });
	
	$('.related-widget-wrapper-link').live('click', function(){
		if (this.href) {
			return showAddAnotherPopup(this);
		} else return false;
	});
  
});
