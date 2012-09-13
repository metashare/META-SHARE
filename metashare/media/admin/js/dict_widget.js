(function($) {
  $(document).ready(function() {
    // add handlers to the delete buttons:
    $('a.kvPairDeleteButton').click(function() {
        var liToRemove = $(this).parent();
        liToRemove.nextAll().find('input,textarea').each(function(){
            $(this).attr('name', $(this).attr('name').replace(
                /(\d+)$/, function(s, n) {return parseInt(n) - 1;}));
          });
        var remainingLis = liToRemove.siblings();
        if (remainingLis.length == 2
            && remainingLis.parent('.pairsRequired').length) {
          remainingLis.first().find('a.kvPairDeleteButton')
            .addClass('kvPairDeleteButtonHidden');
        }
        liToRemove.remove();
      });
    // hide all delete buttons of dictionaries with required key/value pairs
    // that only have one key/value pair:
    $('ul.keyValuePairs.pairsRequired').each(function(){
        var pairs = $(this).children();
        if (pairs.length == 2) {
          pairs.first().find('a.kvPairDeleteButton')
            .addClass('kvPairDeleteButtonHidden');
        }
      });
    // add a handler to the button for adding further key value pairs:
    $('a.kvPairAddButton').click(function() {
        var successor = $(this).parent();
        var list = successor.parent();
        var newEntry = $('<li/>').append(list.next().contents().clone(true));
        var fieldName;
        newEntry.find('input:not(.lang_name),textarea').each(function() {
            fieldName = $(this).attr('name') + (list.children().length - 1);
        	$(this).attr('name', fieldName);
          });
        newEntry.find('input.lang_autocomplete').each(function(){
        	var elem = autocomp_jquery(this);
        	autocomp_my_string(elem);
        });
        newEntry.find('input.lang_name').each(function(){
        	var elem = autocomp_jquery(this);
        	elem.attr('for', fieldName);
        });
        successor.before(newEntry);
        list.find('a.kvPairDeleteButton').removeClass('kvPairDeleteButtonHidden');
      });
  });
})(django.jQuery);
