function addFormHelper(){
  var fields = $('.form_helper').find('input');
  for(var i = 0; i <= fields.size(); i++){
    if($(fields[i]).attr('type') == 'text'){
       $(fields[i]).attr({value: $(fields[i]).attr('defaultText')});
    }
  }

  $('.form_helper').find('input[defaultText]').focusin(
      function(){
        if($(this).attr('type') == 'text'){
          var deftext = $(this).attr("defaultText");
          var text    = $(this).attr("value");
          if(deftext==text){
             $(this).attr({value : ""});
          }
        }
      }
  );

  $('.form_helper').find('input[defaultText]').focusout(
      function(){
          var deftext = $(this).attr("defaultText");
          var text    = $(this).attr("value");
          if(text==""){
             $(this).attr({value : deftext});
          }
      }
  );

  $('.form_helper').submit(
      function(){
        $(this).find('input[defaultText]').each(
            function(){
              var deftext = $(this).attr("defaultText");
              var text    = $(this).attr("value");
              if(text==deftext){
                 $(this).attr({value : ""});
              }
            }
        )
      }
  );
}


// Drop-down menu
var timeout = 500;
var closetimer = 0;
var ddmenuitem = 0;

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
