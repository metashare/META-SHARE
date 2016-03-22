(function($) {
  $(document).ready(function() {
    // add handlers to the delete buttons:
    $('a.kvLangPairDeleteButton').click(function() {
        var liToRemove = $(this).parent();
        liToRemove.nextAll().find('input,textarea').each(function(){
            $(this).attr('name', $(this).attr('name').replace(
                /(\d+)$/, function(s, n) {return parseInt(n) - 1;}));
          });
        liToRemove.nextAll().find('span.lang_name').each(function(){
            $(this).attr('for', $(this).attr('for').replace(
                /(\d+)$/, function(s, n) {return parseInt(n) - 1;}));
          });
        var remainingLis = liToRemove.siblings();
        if (remainingLis.length == 2
            && remainingLis.parent('.pairsRequired').length) {
          remainingLis.first().find('a.kvLangPairDeleteButton')
            .addClass('kvLangPairDeleteButtonHidden');
        }
        liToRemove.remove();
      });
    // hide all delete buttons of dictionaries with required key/value pairs
    // that only have one key/value pair:
    $('ul.keyLangValuePairs.pairsRequired').each(function(){
        var pairs = $(this).children();
        if (pairs.length == 2) {
          pairs.first().find('a.kvLangPairDeleteButton')
            .addClass('kvLangPairDeleteButtonHidden');
        }
      });
    // add a handler to the button for adding further key value pairs:
    $('a.kvLangPairAddButton').click(function() {
        var successor = $(this).parent();
        var list = successor.parent();
        
        // find already used language id values
        var valueList = [];
        list.find('input.lang_autocomplete').each(function(){
        	var value = autocomp_jquery(this).val();
        	valueList.push(value);
        });
        
        var newEntry = $('<li/>').append(list.next().contents().clone(true));
        var fieldName;
        newEntry.find('input,textarea').each(function() {
            var name = $(this).attr('name') + (list.children().length - 1);
            if(name.indexOf('key_') == 0)
            {
            	fieldName = $(this).attr('name') + (list.children().length - 1);
            }
        	$(this).attr('name', name);
          });
        newEntry.find('span.lang_name').each(function(){
        	var elem = autocomp_jquery(this);
        	elem.attr('for', fieldName);
        });
        successor.before(newEntry);
        newEntry.find('input.lang_autocomplete').each(function(){
        	var elem = this;
        	
        	// Avoid proposing an already used value as the default value
        	var element = $(elem);
        	var value = element.val();
        	if(valueList.indexOf(value) != -1)
        	{
        		element.val('');
        	}
        	
        	autocomp_my_string(elem);
        });
        list.find('a.kvLangPairDeleteButton').removeClass('kvLangPairDeleteButtonHidden');
      });
  });
})(django.jQuery);
