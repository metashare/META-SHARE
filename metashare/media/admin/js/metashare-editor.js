// Any javascript required by the META-SHARE editor


django.jQuery(document).ready(function() {

	// Resource editor: content info stuff
  function compute_new_id(prefix) {
	var counter = 0;
    while (true) {
      var existing = django.jQuery('#'+prefix+'-'+counter);
      if (existing.length === 0) break;
      counter++;
    }
    return prefix+'-'+counter;
  }

  function maybe_show_one_more_field(prefix) {
	var new_id = compute_new_id(prefix);
	var new_name = new_id.substr(3); // skip initial 'id_'
	var inputItem = django.jQuery('#'+new_id)
	if (inputItem.length === 0) {
		// need to create it by cloning
		var protodiv = django.jQuery('#'+prefix+'-protodiv');
		var newInput = protodiv.find('input').clone().attr({'id': new_id, 'name': new_name}).css('display', 'inline');
		newInput.change(handle_input_update);
		protodiv.before(newInput);
		var newH1 = protodiv.find('h1').clone();
		var newAdd = newH1.find('a.protoadd').attr('id', 'add_'+new_id).css('display', 'inline');
		var newEdit = newH1.find('a.protoedit').attr('id', 'edit_'+new_id).css('display', 'none');
		protodiv.before(newH1);
	}
  }

  function handle_input_update() {
		var input_id = django.jQuery(this).attr('id');
		var input_value = django.jQuery(this).attr('value');
		var editA = django.jQuery('#edit_' + input_id)
		var addA = django.jQuery('#add_' + input_id)

		if (input_id.localeCompare("has_value") == 0 && django.jQuery('#'+input_id).attr('value')){
			var temp = django.jQuery('#'+input_id).attr('class');
			django.jQuery('a#'+temp).attr('class', '');
		}		
		if (input_value) { // edit
			var protoHref = editA.attr('proto-href');
			editA.attr('href', protoHref+input_value+'/').css('display', 'inline');
			addA.css('display', 'none');
			var prefix = input_id.substr(0, input_id.lastIndexOf('-'));
			if (django.jQuery('#'+prefix+'-protodiv').length > 0) {
				maybe_show_one_more_field(prefix);
			}
		} else { // add
			editA.css('display', 'none');
			addA.css('display', 'inline');
		}
	  }
  
  django.jQuery('#contentInfoStuff input').change(handle_input_update);
  // end of Resource editor: content info stuff
  

 

  // Cancel button
  django.jQuery('input[name="_cancel"]').click(function() {
	  var popup = django.jQuery('input[name="_popup"][value="1"]');
	  if (popup.length > 0) {
		  window.close();
	  } else {
		  window.location = "../";
	  }
  });
  // End of Cancel button

});



// Drop-down menu
var timeout         = 500;
var closetimer		= 0;
var ddmenuitem      = 0;

function jsddm_open()
{	jsddm_canceltimer();
	jsddm_close();
	ddmenuitem = django.jQuery(this).find('ul').eq(0).css('visibility', 'visible');}

function jsddm_close()
{	if(ddmenuitem) ddmenuitem.css('visibility', 'hidden');}

function jsddm_timer()
{	closetimer = window.setTimeout(jsddm_close, timeout);}

function jsddm_canceltimer()
{	if(closetimer)
	{	window.clearTimeout(closetimer);
		closetimer = null;}}

django.jQuery(document).ready(function()
{	django.jQuery('#jsddm > li').bind('mouseover', jsddm_open);
	django.jQuery('#jsddm > li').bind('mouseout',  jsddm_timer);});

document.onclick = jsddm_close;
