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