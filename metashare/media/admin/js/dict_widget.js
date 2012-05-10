(function($) {
  $(document).ready(function() {
    // add a delete button to all key value pairs:
    $('<a href="javascript:void(0)" class="kvPairDeleteButton">Delete entry</a>')
      .appendTo($('ul.keyValuePairs>li,ul.keyValuePairs+div')).click(function() {
          var liToRemove = $(this).parent();
          liToRemove.nextAll().find('input,textarea').each(function(){
              $(this).attr('name', $(this).attr('name').replace(
                  /(\d+)$/, function(s, n) {return parseInt(n) - 1;}));
            });
          var remainingLis = liToRemove.siblings();
          if (remainingLis.length == 2
              && remainingLis.parent('.pairsRequired').length) {
            remainingLis.first().find('a.kvPairDeleteButton').hide();
          }
          liToRemove.remove();
        });
    // hide all delete buttons of dictionaries with required key/value pairs
    // that only have one key/value pair:
    $('ul.keyValuePairs.pairsRequired').each(function(){
        var pairs = $(this).children();
        if (pairs.length == 1) {
          pairs.first().find('a.kvPairDeleteButton').hide();
        }
      });
    // add buttons for adding further key value pairs:
    $('<li><a href="javascript:void(0)" class="kvPairAddButton">Add a new entry</a></li>')
      .appendTo($('ul.keyValuePairs')).find('a').click(function() {
          var successor = $(this).parent();
          var list = successor.parent();
          var newEntry = $('<li/>').append(list.next().contents().clone(true));
          newEntry.find('input,textarea').each(function() {
              $(this).attr('name',
                $(this).attr('name') + (list.children().length - 1));
            });
          successor.before(newEntry);
          list.find('a.kvPairDeleteButton').show();
        });
  });
})(django.jQuery);
