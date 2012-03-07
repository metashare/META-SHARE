
$(document).ready(function(){
	/* handler for scrolling page to top */
	$(".scroll").click(function(event){
		event.preventDefault();
		var full_url = this.href;
		var parts = full_url.split("#");
		var trgt = parts[1];
		var target_offset = $("#"+trgt).offset();
		var target_top = target_offset.top;
		$('html, body').animate({scrollTop:target_top-500}, 500);
	});
	
	
});

function show_more_details(){
	$('#more_details_button').hide();
	$('#less_details_button').show();	
	$('#more_details').slideDown();

}
function show_less_details(){
	$('#more_details_button').show();
	$('#less_details_button').hide();	
	$('#more_details').slideUp();

}

function check_agree_box(){
console.log(document.agree.elements[0].checked);
	if (document.agree.elements[0].checked){
		$('#accept_button').slideDown();	
	}else{
		$('#accept_button').slideUp();
	}
}


function show_advanced_search(){
	if($('#advanced_search_panel').is(":visible")){
		$('#advanced_search_panel').slideUp();
		$('#advanced_search').removeClass("search_hover");	
	}
	else{
		$('#advanced_search_panel').slideDown();
		var target_offset = $("#advanced_search_panel").offset();
		var target_top = target_offset.top;
		$('html, body').animate({scrollTop:target_top-220}, 500);
		$('#type_field').focus();
		
		$('#advanced_search').addClass("search_hover");	
	}
}

function addFormHelper(){
  var fields = $('.form_helper').find('input');
  for(var i = 0; i <= fields.size(); i++){
    if($(fields[i]).attr('type') == 'text'){
       $(fields[i]).attr({value: $(fields[i]).attr('defaultText')});
    }
  }

  $('.form_helper').find('input').focusin(
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

  $('.form_helper').find('input').focusout(
      function(){
          var deftext = $(this).attr("defaultText");
          var text    = $(this).attr("value");
          if(text==""){
             $(this).attr({value : deftext});
          }
      }
  );
}