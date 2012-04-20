/*
 * From http://djangosnippets.org/snippets/2564/
 */

function dismissEditRelatedPopup(win, objId, newRepr) {
	objId = html_unescape(objId);
	newRepr = html_unescape(newRepr);
	newRepr = newRepr.replace(/</g, '&lt;');
	newRepr = newRepr.replace(/>/g, '&gt;');
	var name = windowname_to_id(win.name).replace(/^edit_/, '');;
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
	win.close();
};

if (!dismissAddAnotherPopup.original) {
	var originalDismissAddAnotherPopup = dismissAddAnotherPopup;
	dismissAddAnotherPopup = function(win, newId, newRepr) {
		originalDismissAddAnotherPopup(win, newId, newRepr);
		newId = html_unescape(newId);
		newRepr = html_unescape(newRepr);
		var id = windowname_to_id(win.name);
		$('#' + id).trigger('change');
	};
	dismissAddAnotherPopup.original = originalDismissAddAnotherPopup;
}

django.jQuery(document).ready(function() {
  
  var $ = $ || jQuery || django.jQuery;
  var changeSelector = '.related-widget-wrapper-change-link';
  var addSelector = '.related-widget-wrapper-add-link';
  var deleteSelector = '.related-widget-wrapper-delete-link';
  var hrefTemplateAttr = 'data-href-template';
  
  $('.related-widget-wrapper').live('change', function(){
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
