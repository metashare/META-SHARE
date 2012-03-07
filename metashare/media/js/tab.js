
$(document).ready(function()
{
	return;
})

function setupTabs(jqDestElem)
{
	return;
	var jqHiddenDiv = $('<div style="display: none"></div>');
	$('body').append(jqHiddenDiv);
	
	jqDestElem.find('.tabbed').each(function(index, domElem){
		var jqInfo = $(domElem);
		var jqParent = jqInfo.parent();
		jqInfo.detach().appendTo(jqHiddenDiv);
		var ts2 = new tabSet(jqInfo, 'idDest', jqParent);
	});
	/*
	var jqResInfo = $('#fmId_ResourceInfo');
	jqResInfo.detach().appendTo(jqHiddenDiv);
	
	var ts2 = new tabSet('fmId_ResourceInfo', 'idDest');
	*/
}

var tabSet_templ = '\
<span class="tabset">\
	<span class="tabHeader">\
		<span class="li">\
			<span class="a">\
			</span>\
		</span>\
		<span class="last">\
		</span>\
	</span>\
	<span class="tabBody">\
	</span>\
</span>\
';

/*
*/
var tabSet = function(jqTabset, form, jqParent)
{
	this.jqTabset = jqTabset;
	this.form = form;
	this.jqElem = null;
	this.jqTabTempl = null;
	this.tabItems = [];
	this.jqTabBody = null;
	this.currentTab = null;
	this.currentStyle = 'stile1';
	this.jqParent = jqParent;
	
	this.addTab = function(jqTabInfoItem, index)
	{
		var objThis = this;
		var jqTabItem = this.jqTabTempl.clone(true);
		var tabItem = new tab(jqTabItem, jqTabInfoItem, objThis, index);
		this.tabItems[this.tabItems.length] = tabItem;
		this.jqElem.find('.tabHeader').find('.last').before(jqTabItem);
	}
	
	this.addTabs = function()
	{
		var obj = this;
		this.jqTabset.children('div.formgroupBody').children().each(function(index, domElem){
			obj.addTab($(domElem), index);
		});
	}
	
	this.tabSelected = function(tabObj)
	{
		//this.jqTabBody.empty();
		if(this.currentTab != null)
		{
			this.tabItems[this.currentTab].deselect();
			this.tabItems[this.currentTab].jqTabPage.detach().appendTo(this.tabItems[this.currentTab].jqTabInfoItem);
		}
		this.currentTab = tabObj.index;
		this.tabItems[this.currentTab].select();
		tabObj.jqTabPage.detach().appendTo(this.jqTabBody);
	}
	
	this.highlightTab = function(index)
	{
		this.tabItems[index].highlight();
	}
	
	this.init = function()
	{
		this.jqElem = $(tabSet_templ);
		this.jqElem.addClass(this.currentStyle);
		this.jqElem.find('.tabHeader').addClass(this.currentStyle);
		this.jqElem.find('.tabBody').addClass(this.currentStyle);
		this.jqTabTempl = this.jqElem.find('.li');
		this.jqTabTempl.remove();
		this.jqTabBody = this.jqElem.find('.tabBody');
		
		this.addTabs();
		
		if(this.tabItems.length > 0)
		{
			this.currentTab = 0;
			this.tabItems[this.currentTab].tabSelect();
		}
		
		this.jqParent.append(this.jqElem);
	}
	
	this.init();
}

var tab = function(jqTabItem, jqTabInfoItem, tabset, index)
{
	this.jqElem = jqTabItem;
	this.jqTabInfoItem = jqTabInfoItem;
	this.tabset = tabset;
	this.index = index;
	this.tabName = null;
	this.jqTabPage = null;
	
	this.showPage = function()
	{
	}
	
	this.hidePage = function()
	{
	}
	
	this.highlight = function()
	{
		this.jqElem.addClass('highlight');
	}
	
	this.tabSelect = function()
	{
		var objThis = this;
		this.tabset.tabSelected(objThis);
	}
	
	this.select = function()
	{
		this.jqElem.addClass('selected');
	}
	
	this.deselect = function()
	{
		this.jqElem.removeClass('selected');
	}
	
	this.init = function()
	{
		var objThis = this;
		//this.tabName = this.jqTabInfoItem.attr('tabName');
		var jqHeader = this.jqTabInfoItem.children('span.formHeader,div.formgroupHeader,div.formsetTitle');
		this.tabName = jqHeader.children('span.formName,span.formGroupName,span.formsetName').html();
		if(this.tabName.indexOf('_') > 0)
		{
			var index = this.tabName.indexOf('_');
			this.tabName = this.tabName.substring(0, index);
		}
		if(this.tabName.indexOf('Info') > 0)
		{
			var index = this.tabName.indexOf('Info');
			this.tabName = this.tabName.substring(0, index);
		}
		this.jqElem.find('.a').html(this.tabName);
		this.jqElem.find('.a').click(function(){
			objThis.tabset.tabSelected(objThis);
		});
		this.jqTabPage = this.jqTabInfoItem.children('div.formBody,div.formgroupBody,div.formsetBody');
	}
	
	this.init();
}
