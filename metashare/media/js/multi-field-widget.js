// Delete current container if there is still one other container left.
function delete_container(widget_id, id) {
    var containers = django.jQuery('#widget_'+widget_id+' li.container[id]');

    if (containers.length > 1) {
        django.jQuery('#container_'+widget_id+'_'+id).remove();
        reset_indexes(widget_id, id);
    } else {
    	django.jQuery('#container_'+widget_id+'_'+id+' .input').val('');
    }
}

// Reset indexes sequentially
function reset_indexes(widget_id, id) {
    var containers = django.jQuery('#widget_'+widget_id+' li.container');

    if (containers.length > 0) {
        for(var i = 0; i < containers.length - 1; i++) {
        	var container = django.jQuery(containers.get(i));
        	var cont_id = 'container_' + widget_id + '_' + i;
        	container.attr('id', cont_id);
        	var a = container.find('a');
        	var href = 'javascript: delete_container(' + widget_id + ', ' + i + ');';
        	a.attr('href', href);
        }
    }
}

// Computes the smallest identifier for the next container.
function compute_next_id(widget_id) {
    var containers = django.jQuery('#widget_'+widget_id+' li.container');
    var id = containers.length;

    for (var i = 0; i < containers.length; i++) {
        var input = django.jQuery('#container_'+widget_id+'_'+i+' .input');
        if (input.length === 0 || input.val() === '') {
            return i;
        }
    }

    return id;
}

// Add new container including delete link and input widget.
function add_container(widget_id) {
    var id = compute_next_id(widget_id);
    var input = django.jQuery('#container_'+widget_id+'_'+id+' .input');
    // check if the container will manage language variants. We do this because
    //each selection determines the available options for the next selection

    if (input.length === 0) {
        // First, we clone the empty_widget for this widget id and turn it
        // into an active container with a correct container id.
        var new_container = django.jQuery('#empty_widget_'+widget_id).clone();
        new_container.attr('class', 'container');
        new_container.attr('id', 'container_'+widget_id+'_'+id);
        
        // Then, we patch the href attribute to enable proper deletion.
        var action = 'javascript:delete_container('+widget_id+','+id+');';
        var deletelink = new_container.find('a');
        deletelink.attr('href', action);
        
        // Add the cloned input before the current add button.
        django.jQuery('#add_button_'+widget_id).parent().before(new_container);
        
        // If available, turn the <div class="script"> into a <script> and
        // update the function parameter, in order to add autocomplete
        // functionalities to the text field
        var scr_div = new_container.find('div[class="script"]');
        if(scr_div)
        {
        	var scr_content = scr_div.text();
        	var scr = django.jQuery('<script></script>');
        	// Compute the field ID based on both the widget_id and the field number
        	scr_content = scr_content.replace(/container_\d+___ID__/, 'container_' + widget_id + '_' + id);
        	scr.text(scr_content);
        	scr_div.replaceWith(scr);
        	
        }
        
        // And put a reference into input.
        input = django.jQuery('#container_'+widget_id+'_'+id+' .input');

    }
    //call the update variants function only for language variants
    if(new_container.closest(".form-row").attr("class")=='form-row variant'){
      update_var_variants(new_container.prev("li"), new_container);
    }
    input.focus();
}

var setWidgetId = function(jqElem, idNumber)
{
	var widgetId = 'widget_' + idNumber;
	jqElem.attr('id', widgetId);
	
	// <li> with text field
	jqElem.find('li.container[id]').each(function(liIndex, liElem){
		var liId = $(liElem).attr('id');
		$(liElem).attr('id', 'container_' + idNumber + '_' + liIndex);
		$(liElem).find('a').attr('href', 'javascript:delete_container(' + idNumber + ', ' + liIndex + ');')
	});
	
	// <li> 'Add another field'
	jqElem.find('li.container:not([id])').each(function(liIndex, liElem){
		$(liElem).find('a').attr('id', 'add_button_' + idNumber).attr('href', 'javascript:add_container(' + idNumber + ');')
	});
	
	// Empty element
	jqElem.find('li.empty_widget').each(function(liIndex, liElem){
		$(liElem).attr('id', 'empty_widget_' + idNumber);
		$(liElem).find('a').attr('href', 'javascript:delete_container(' + idNumber + ');')
	});
}

var lastMultifieldWidgetId = 0;

var getNextMultifieldWidgetId = function()
{
	lastMultifieldWidgetId++;
	return lastMultifieldWidgetId;
}

django.jQuery(document).ready(function() {
	/*
	 * Force id of multifield widgets to be unique.
	 */
	var $ = django.jQuery;
	
	$('body').find('ul.multifield_list').each(function(index, elem){
		var wId = getNextMultifieldWidgetId();
		setWidgetId($(elem), wId);
	});


    $(this).find(".form-row.languageName select").each(
        function () {
            update_lang_variants($(this));
        }
    );

    $(this).find(".form-row.languageScript select").each(
        function () {
                update_lang_variants_with_script($(this));
        }
    );

    $(this).find(".variant select").each(
        function () {
                update_var_variants($(this), $(this).parent().next("li"));
        }
    );

    $(this).find(".form-row.languageName select").change(
        function () {
            $(this).parent().parent().siblings(".languageScript").find("select").val("");
            if ($(this).parent().parent().siblings(".variant").find("select").length > 1) {
                $(this).parent().parent().parent().find("li[id*='container']:not(:first)").remove();
            }
            update_lang_variants($(this));
        }
    );

    $(this).find(".form-row.languageScript select").change(
        function () {
            //if ($(this).parent().parent().siblings(".variants").find("select").length > 1) {
            //    $(this).parent().parent().parent().find("li[id*='container']:not(:first)").remove();
            //}
            update_lang_variants_with_script($(this));
        }
    );

    $(this).find(".variant select").change(
        function () {
            //if($(this).parent().next("li").attr("id") != null){
                update_var_variants($(this), $(this).parent().next("li"));
            //}
        }
    );
});


function update_lang_variants(e) {
    var root = $(e).closest(".module.aligned");
    var variants = root.find(".variant:first");
    var selected = variants.find("select option:selected").val();
    if (e.val() != "") {
        $.ajax({
            url: "/update_lang_variants/",
            type: 'POST',
            data: {'lang': e.val()},
            success: function (result) {
                vars = result.split("//");
                selElement = variants.find("select:first");
                selElement.empty();
                selElement.append($("<option></option>").
                    attr("value", "").text("--------"));
                for (var r in vars) {
                    selElement.append($("<option></option>").
                        attr("value", vars[r]).text(vars[r]));
                }
                selElement.val(selected);
            }
        })
    };
}

function update_lang_variants_with_script(e) {
    var root = $(e).closest(".module.aligned");
    var variants = root.find(".variant:first");
    var selected = variants.find("select option:selected").val();
    if (e.val() != "") {
        $.ajax({
            url: "/update_lang_variants_with_script/",
            type: 'POST',
            data: {'script': e.val(), 'lang': e.parent().parent().prev(".languageName").find("select option:selected").val()},
            success: function (result) {
                vars = result.split("//");
                selElement = variants.find("select:first");
                selElement.empty();
                selElement.append($("<option></option>").
                    attr("value", "").text("--------"));
                for (var r in vars) {
                    selElement.append($("<option></option>").
                        attr("value", vars[r]).text(vars[r]));
                }
                selElement.val(selected);
            }
        })
    };
}

function update_var_variants(prevRef, element) {
    var selElement = element.find("select:first");
    var selected = element.find("select option:selected").val();
    var param = prevRef.find("option:selected").val();
    var dataValue = prevRef.find("option:selected").val();
    if (param != "") {
        $.ajax({
            url: "/update_var_variants/",
            type: 'POST',
            data: {'variant': unescape(dataValue)},
            contentType: "text/html; charset=utf-8",
            success: function (result) {
                vars = result.split("//");
                selElement.empty();
                selElement.append($("<option></option>").
                    attr("value", "").text("--------"));
                for (var r in vars) {
                    selElement.append($("<option></option>").
                        attr("value", vars[r]).text(vars[r]));
                }
                selElement.val(selected);
                //if (result.length) {
                //    selElement.parent().show().prop('disabled', false);
                //    selElement.parent().next("li").has("a").prop('disabled', false);
                //}
                //else {
                //    selElement.parent().next("li").has("a").prop('disabled', true);
                //    selElement.parent().hide().prop('disabled', true);
                //}
            }
        })
    };
}

