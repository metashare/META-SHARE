/*
 * django-selectable UI widget
 * Source: https://bitbucket.org/mlavin/django-selectable
 * Docs: http://django-selectable.readthedocs.org/
 *
 * Depends:
 *   - jQuery 1.4.3+
 *   - jQuery UI 1.8 widget factory
 *
 * Copyright 2010-2012, Mark Lavin
 * BSD License
 *
*/
(function($) {
	$.widget("ui.djselectable", {
        options: {
            removeIcon: "ui-icon-close",
            editIcon: "ui-icon-pencil",
            comboboxIcon: "ui-icon-triangle-1-s",
            prepareQuery: null,
            highlightMatch: true,
            formatLabel: null
        },

        _initDeck: function() {
            /* Create list display for currently selected items for multi-select */
            var self = this;
            var data = $(this.element).data();
            var style = data.selectablePosition || data['selectable-position'] || 'bottom';
            this.deck = $('<ul>').addClass('ui-widget selectable-deck selectable-deck-' + style);
            if (style === 'bottom' || style === 'bottom-inline') {
                $(this.element).after(this.deck);
            } else {
                //$(this.element).before(this.deck);
                $(this.searchIcon).before(this.deck);
            }
            $(self.hiddenMultipleSelector).each(function(i, input) {
                self._addDeckItem(input);
            });
        },
        
        _handleAlignment: function() {
            /* Handle correct alignment */
            if(this.deck.hasClass('selectable-deck-top'))
            {
                var jqLab = $(this.deck.parent().children('label').get(0));
                var jqImg = $(this.deck.parent().children('img').get(0));
                var labBottom = jqLab.position().top + jqLab.height();
                var deckBottom = this.deck.position().top + this.deck.height() + parseInt(this.deck.css('margin-bottom'));
                var imgTop = jqImg.position().top;
                if(deckBottom < labBottom)
                {
                	jqImg.css('margin-left', 0);
                	jqImg.css('padding-left', 0);
                }
                else
                {
                	var mgLeft = this.deck.css('margin-left');
                	var pdLeft = this.deck.css('padding-left');
                	jqImg.css('margin-left', mgLeft);
                	jqImg.css('padding-left', pdLeft);
                }
            }
            
        },

        _addDeckItem: function(input) {
            /* Add new deck list item from a given hidden input */
            var self = this;
            var recId = $(input).attr('value');
            var title = $(input).attr('title');
            var jqItem = $('<li>')
            .attr('val_id', recId)
            .append($('<span>').addClass('title').text(title))
            .addClass('selectable-deck-item')
            .appendTo(this.deck)
            .append(
                $('<div>')
                .addClass('selectable-deck-remove')
                .append(
                    $('<a>')
                    .attr('href', '#')
                    .append(
                    	$('<img>')
                    	.attr('src', window.__admin_media_prefix__ + 'img/admin/icon_deletelink.gif')
                    	.attr('width', '10px')
                    	.attr('height', '10px')
                    	.attr('alt', 'Delete related model')
                    )
                    .click(function() {
                        if(self.allowEditing)
                        {
                        	var isSure = confirm("Are you sure you want to remove this item from the list?");
                        	if(!isSure)
                        	{
                        		return false;
                        	}
                        }
                    	$(input).remove();
                        $(this).closest('li').remove();
                        self._handleAlignment();
                        return false;
                    })
                )
            );
            self._handleAlignment();
            
            if(self.isSubclassable)
            {
                var modelClass = $(input).attr('model-class');
                if(modelClass)
                {
                	var editingUrl = self.baseUrl + modelClass;
                	$(input).attr('editing-url', editingUrl);
                }
            }
            if(self.allowEditing && ((self.baseEditingUrl != null) || self.isSubclassable))
            {
                jqItem.append(
                        $('<div>')
                        .addClass('selectable-deck-edit')
                        .append(
                            $('<a>')
                            .attr('href', '#')
                           	.css('margin-right', '4px')
                            .append(
                            	$('<img>')
                            	.attr('src', window.__admin_media_prefix__ + 'img/admin/icon_changelink.gif')
                            	.attr('width', '10px')
                            	.attr('height', '10px')
                            	.attr('alt', 'Edit related model')
                            )
                            .click(function() {
                                var recId = $(input).attr('value');
                                var link = null;
                                if(self.isSubclassable)
                                {
                                    link = $(input).attr('editing-url') + "/" + recId + "/";
                                }
                                else
                                {
                                    link = self.baseEditingUrl + "/" + recId + "/";
                                }
                                var name = 'id_' + self.textName;
                                showEditPopup(link, name, self);
                                return false;
                            })
                        )
                    );
            }
        },

        select: function(item) {
            /* Trigger selection of a given item.
            Item should contain two properties: id and value */
            var self = this,
            input = this.element;
            $(input).removeClass('ui-state-error');
            if (item) {
                if (self.allowMultiple) {
                    $(input).val("");
                    $(input).data("autocomplete").term = "";
                    if ($(self.hiddenMultipleSelector + '[value=' + item.id + ']').length === 0) {
                        var newInput = $('<input />', {
                            'type': 'hidden',
                            'name': self.hiddenName,
                            'value': item.id,
                            'title': item.value,
                            'data-selectable-type': 'hidden-multiple',
                            'model-class': item.cls
                        });
                        $(input).after(newInput);
                        self._addDeckItem(newInput);
                        /* Clear the input text again after some time since
                         * some other event handler tries to set the selected value
                         */
                        setTimeout(function(){
                        	$(input).val("");
                        }, 200);
                        return false;
                    }
                } else {
                    $(input).val(item.value);
                    var ui = {item: item};
                    $(input).trigger('autocompleteselect', [ui ]);
                }
            }
        },

        showThrobber: function() {
        	var self = this;
        	if(self.throbberImg)
        	{
            	$(self.searchIcon).attr('src', self.throbberImg);
        	}
        },
        
        hideThrobber: function() {
        	var self = this;
        	$(self.searchIcon).attr('src', self.searchImg);
        },
        
        _create: function() {
            /* Initialize a new selectable widget */
            var self = this,
            input = this.element,
            data = $(input).data();
            self.allowNew = data.selectableAllowNew || data['selectable-allow-new'];
            self.isSubclassable = data.selectableIsSubclassable || data['selectable-is-subclassable'];
            self.allowEditing = data.selectableAllowEditing || data['selectable-allow-editing'];
            self.baseUrl = data.selectableBaseUrl || data['selectable-base-url'];
            self.throbberImg = data.selectableThrobberImg || data['selectable-throbber-img'];
            self.useStateError = data.selectableUseStateError;// || data['selectable-use-state-error'];
            if(self.useStateError == undefined) {
            	self.useStateError = true;
            }
            self.baseEditingUrl = null;
            var jqParent = $(input).parent();
            var jqA = jqParent.find('a');
            self.searchIcon = jqParent.children('img').get(0);
            self.searchImg = $(self.searchIcon).attr('src');
            var href = jqA.attr('href');
            if(href)
            {
            	self.baseEditingUrl = href.replace(/\/add\//, '');
            }
            self.allowMultiple = data.selectableMultiple || data['selectable-multiple'];
            self.textName = $(input).attr('name');
            self.hiddenName = self.textName.replace('_0', '_1');
            self.hiddenSelector = ':input[data-selectable-type=hidden][name=' + self.hiddenName + ']';
            self.hiddenMultipleSelector = ':input[data-selectable-type=hidden-multiple][name=' + self.hiddenName + ']';
            if (self.allowMultiple) {
                self.allowNew = false;
                $(input).val("");
                this._initDeck();
            }

            function dataSource(request, response) {
                /* Custom data source to uses the lookup url with pagination
                Adds hook for adjusting query parameters.
                Includes timestamp to prevent browser caching the lookup. */
                var url = data.selectableUrl || data['selectable-url'];
                var now = new Date().getTime();
                var query = {term: request.term, timestamp: now};
                if (self.options.prepareQuery) {
                    self.options.prepareQuery(query);
                }
                var page = $(input).data("page");
                if (page) {
                    query.page = page;
                }
				//$.getJSON(url, query, response);
                $(self.element).removeClass('ui-state-not-found');
				$.getJSON(url, query, function(data, status){
					response(data, status);
					if(!data.length) {
						// highlight the input element if no data was found
						$(self.element).addClass('ui-state-not-found');
					}
					self.hideThrobber();
				});
            }
            // Create base auto-complete lookup
            $(input).autocomplete({
                source: dataSource,
                change: function(event, ui) {
                    $(input).removeClass('ui-state-error');
                    if ($(input).val() && !ui.item) {
                        if (!self.allowNew) {
                            if(self.useStateError) {
                            	$(input).addClass('ui-state-error');
                            }
                        }
                    }
                    if (self.allowMultiple && !$(input).hasClass('ui-state-error')) {
                        $(input).val("");
                        $(input).removeClass('ui-state-not-found');
                        $(input).data("autocomplete").term = "";
                    }
                },
                select: function(event, ui) {
                    $(input).removeClass('ui-state-error');
                    if (ui.item && ui.item.page) {
                        // Set current page value
                        $(input).data("page", ui.tem.page);
                        $('.selectable-paginator', self.menu).remove();
                        // Search for next page of results
                        $(input).autocomplete("search");
                        return false;
                    }
                    self.select(ui.item);
                },
                search: function(event, ui){
                	self.showThrobber();
                },
                open: function(event, ui){
                	self.hideThrobber();
                }
            }).addClass("ui-widget ui-widget-content ui-corner-all");
            // Override the default auto-complete render.
            $(input).data("autocomplete")._renderItem = function(ul, item) {
                /* Adds hook for additional formatting, allows HTML in the label,
                highlights term matches and handles pagination. */
                var label = item.label;
                if (self.options.formatLabel) {
                    label = self.options.formatLabel(label, item);
                }
                if (self.options.highlightMatch) {
                    var re = new RegExp("(?![^&;]+;)(?!<[^<>]*)(" +
                    $.ui.autocomplete.escapeRegex(this.term) +
                    ")(?![^<>]*>)(?![^&;]+;)", "gi");
                    label = label.replace(re, "<span class='highlight'>$1</span>");
                }
                var li =  $("<li></li>")
                    .data("item.autocomplete", item)
                    .append($("<a></a>").append(label))
                    .appendTo(ul);
                if (item.page) {
                    li.addClass('selectable-paginator');
                }
                return li;
            };
            // Override the default auto-complete suggest.
            $(input).data("autocomplete")._suggest = function(items) {
                /* Needed for handling pagination links */
                var page = $(input).data('page');
                var ul = this.menu.element;
                if (!page) {
                    ul.empty();
                }
                $(input).data('page', null);
                ul.zIndex(this.element.zIndex() + 1);
                this._renderMenu(ul, items);
                this.menu.deactivate();
                this.menu.refresh();
                // size and position menu
                ul.show();
                this._resizeMenu();
                ul.position($.extend({of: this.element}, this.options.position));
                if (this.options.autoFocus) {
                    this.menu.next(new $.Event("mouseover"));
                }
            };
            
            // Remove 'not-found' state when the input is cleared
            $(input).bind('keyup', function(){
            	if($(input).val() == '') {
            		$(input).removeClass('ui-state-not-found');
            	}
            });
            
            // Additional work for combobox widgets
            var selectableType = data.selectableType || data['selectable-type'];
            if (selectableType === 'combobox') {
                // Change auto-complete options
                $(input).autocomplete("option", {
                    delay: 0,
                    minLength: 0
                })
                .removeClass("ui-corner-all")
                .addClass("ui-corner-left ui-combo-input");
                // Add show all items button
                $("<button>&nbsp;</button>").attr("tabIndex", -1).attr("title", "Show All Items")
                .insertAfter($(input))
                .button({
                    icons: {
                        primary: self.options.comboboxIcon
                    },
                    text: false
                })
                .removeClass("ui-corner-all")
                .addClass("ui-corner-right ui-button-icon ui-combo-button")
                .click(function() {
                    // close if already visible
                    if ($(input).autocomplete("widget").is(":visible")) {
                        $(input).autocomplete("close");
                        return false;
                    }
                    // pass empty string as value to search for, displaying all results
                    $(input).autocomplete("search", "");
                    $(input).focus();
                    return false;
                });
            }
        }
	});
})(jQuery);


function bindSelectables(context) {
    /* Bind all selectable widgets in a given context.
    Automatically called on document.ready.
    Additional calls can be made for dynamically added widgets.
    */
    $(":input[data-selectable-type=text]", context).djselectable();
    $(":input[data-selectable-type=combobox]", context).djselectable();
    $(":input[data-selectable-type=hidden]", context).each(function(i, elem) {
        var hiddenName = $(elem).attr('name');
        var textName = hiddenName.replace('_1', '_0');
        $(":input[name=" + textName + "][data-selectable-url]").bind(
            "autocompletechange autocompleteselect",
            function(event, ui) {
                if (ui.item && ui.item.id) {
                    $(elem).val(ui.item.id);
                } else {
                    $(elem).val("");
                }
            }
        );
    });
}

/* Monkey-patch Django's dynamic formset, if defined */
if (typeof(django) !== "undefined" && typeof(django.jQuery) !== "undefined") {
    if (django.jQuery.fn.formset) {
        var oldformset = django.jQuery.fn.formset;
        django.jQuery.fn.formset = function(opts) {
            var options = $.extend({}, opts);
            var addedevent = function(row) {
                bindSelectables($(row));
            };
            var added = null;
            if (options.added) {
                // Wrap previous added function and include call to bindSelectables
                var oldadded = options.added;
                added = function(row) { oldadded(row); addedevent(row); };
            }
            options.added = added || addedevent;
            return oldformset.call(this, options);
        };
    }
}

/* Monkey-patch Django's dismissAddAnotherPopup(), if defined */
if (typeof(dismissAddAnotherPopup) !== "undefined" && typeof(windowname_to_id) !== "undefined" && typeof(html_unescape) !== "undefined") {
    var django_dismissAddAnotherPopup = dismissAddAnotherPopup;
    dismissAddAnotherPopup = function(win, newId, newRepr, newClass) {
        /* See if the popup came from a selectable field.
           If not, pass control to Django's code.
           If so, handle it. */
        var fieldName = windowname_to_id(win.name); /* e.g. "id_fieldname" */
        var field = $('#' + fieldName);
        var multiField = $('#' + fieldName + '_0');
        /* Check for bound selectable */
        var singleWidget = field.data('djselectable');
        var multiWidget = multiField.data('djselectable');
        if (singleWidget || multiWidget) {
            // newId and newRepr are expected to have previously been escaped by
            // django.utils.html.escape.
            if(!newClass)
            {
            	/*
            	 * Default value since, for this class, the model name
            	 * will not be set on the server side.
            	 */
            	newClass = 'documentunstructuredstring_model'
            }
        	var item =  {
                id: html_unescape(newId),
                value: html_unescape(newRepr),
                cls: html_unescape(newClass)
            };
            if (singleWidget) {
                field.djselectable('select', item);
            }
            if (multiWidget) {
                multiField.djselectable('select', item);
            }
            win.close();
        } else {
            /* Not ours, pass on to original function. */
            return django_dismissAddAnotherPopup(win, newId, newRepr);
        }
    };
}

$(document).ready(function() {
    // Bind existing widgets on document ready
	if (typeof(djselectableAutoLoad) === "undefined" || djselectableAutoLoad) {
        bindSelectables('body');
    }
});

var lastWidget = null;
var testIframe = false;

function showEditPopup(href, name, widget)
{
    lastWidget = widget;
	if (href.indexOf('?') == -1) {
        href += '?_popup_o2m=1';
    } else {
        href  += '&_popup_o2m=1';
    }
    if(!testIframe)
    {
    	href += '&_caller=opener'
    	var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        win.focus();
    }
    else
    {
    	href += '&_caller=top'
    	openDialog(href);
    }
    return false;
}

function dismissEditPopup(win, objId, newRepr)
{
	var jqLi = lastWidget.deck.find('li[val_id=' + objId + ']');
	var jqSpan = jqLi.find('span.title');
	jqSpan.text(newRepr);
	if(!testIframe)
	{
		win.close();
	}
	else
	{
		closeDialog();
	}
}


//Test

var jqDialog = null;

function openDialog(href)
{
	jqDialog = $("<div>");
	jqDialog.addClass("dialog");
	var dialogOpts = {"modal": true, "width": "800", "height": "500"};
	jqIframe = $("<iframe>");
	jqIframe.css('width', '100%').css('height', '100%')
	jqIframe.attr("src", href);
	jqDialog.append(jqIframe);
	$("body").append(jqDialog);
	jqDialog.dialog(dialogOpts);
}

function closeDialog()
{
	jqIframe.remove();
	jqIframe = null;
	if(jqDialog != null)
	{
		jqDialog.remove();
		jqDialog = null;
	}
}

