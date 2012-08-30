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
        	scr_content = scr_content.replace('__ID__', id)
        	scr.text(scr_content);
        	scr_div.replaceWith(scr);
        	
        }
        
        // And put a reference into input.
        input = django.jQuery('#container_'+widget_id+'_'+id+' .input');
    }

    input.focus();
}