function createNewSubInstance(select, proto_name, proto_href) {
    var selected_subclass = select.val();
    if (selected_subclass != '') {
        var name = proto_name.replace(/^add_/, '');
        name = id_to_windowname(name);

        href = proto_href + '/' + selected_subclass + '/add/';
        if (href.indexOf('?') == -1) {
            href += '?_popup=1';
        } else {
            href  += '&_popup=1';
        }
        var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        if (win != undefined) {
            win.focus();
        }
        else {
            alert('Could not open popup window!\nMaybe there\'s a popup '
              + 'blocker runnning?');
        }
        // Salvatore: reset the empty value so that the 'onchange' event
        // is correctly triggered (see comment in SingleChoiceTypeWidget.render in
        // file 'metashare/repository/editor/widgets.py').
        select.val("");
        
        // cfedermann: why not directly trigger the onchange event?
        //
        // select.trigger('change');
        
        return false;
    }
}

