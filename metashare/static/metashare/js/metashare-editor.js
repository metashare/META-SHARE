// Any javascript required by the META-SHARE editor


$(document).ready(function() {

	// Resource editor: content info stuff
  function compute_new_id(prefix) {
	var counter = 0;
    while (true) {
      var existing = $('#'+prefix+'-'+counter);
      if (existing.length === 0) break;
      else {
    	  var edit = $('#edit_'+prefix+'-'+counter);
    	  var href = edit.attr('href');
    	  if(!href) break;
      }
      counter++;
    }
    return prefix+'-'+counter;
  }

  function maybe_show_one_more_field(prefix) {
	var new_id = compute_new_id(prefix);
	var new_name = new_id.substr(3); // skip initial 'id_'
	var inputItem = $('#'+new_id);
	if (inputItem.length === 0) {
		// need to create it by cloning
		var protodiv = $('#'+prefix+'-protodiv');
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
		var input_id = $(this).attr('id');
		var input_value = $(this).attr('value');
		var editA = $('#edit_' + input_id)
		var addA = $('#add_' + input_id)

		if (input_id.localeCompare("has_value") == 0 && $('#'+input_id).attr('value')){
			var temp = $('#'+input_id).attr('class');
			$('a#'+temp).attr('class', '');
		}		
		if (input_value) { // edit
			var protoHref = editA.attr('proto-href');
			editA.attr('href', protoHref+input_value+'/').css('display', 'inline');
			addA.css('display', 'none');
			var prefix = input_id.substr(0, input_id.lastIndexOf('-'));
			//for every input with this name, remove error class from all menu items
			if(prefix){				
				$("input[name^='" + prefix.substr(3) + "-']").each(function(){
					$(this).next("h1").children("a").removeClass("error");
				});					
			}			
			if ($('#'+prefix+'-protodiv').length > 0) {
				maybe_show_one_more_field(prefix);				
			}
		} else { // add
			editA.css('display', 'none');
			addA.css('display', 'inline');
		}
		
	  }
  
  $('#contentInfoStuff input').change(handle_input_update);
  // end of Resource editor: content info stuff
  

 

  // Cancel button
  $('input[name="_cancel"]').click(function() {
	  var popup = $('input[name="_popup"][value="1"]');
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
	ddmenuitem = $(this).find('ul').eq(0).css('visibility', 'visible');}

function jsddm_close()
{	if(ddmenuitem) ddmenuitem.css('visibility', 'hidden');}

function jsddm_timer()
{	closetimer = window.setTimeout(jsddm_close, timeout);}

function jsddm_canceltimer()
{	if(closetimer)
	{	window.clearTimeout(closetimer);
		closetimer = null;}}

$(document).ready(function()
{	$('#jsddm > li').bind('mouseover', jsddm_open);
	$('#jsddm > li').bind('mouseout',  jsddm_timer);});

document.onclick = jsddm_close;
