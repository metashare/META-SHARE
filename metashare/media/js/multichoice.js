/*
Project: META-SHARE prototype implementation
 Author: Salvatore Minutoli <salvatore.minutoli@iit.cnr.it>
*/


// Window to be used to detect clicks out of the list
var outWin = null;

function initOutWin()
{
	if(outWin != null)
	{
		return;
	}
	
	outWin = $('<div id="outside"></div>');
	outWin.css('position', 'absolute');
	outWin.css('top', 0);
	outWin.css('left', 0);
	outWin.css('width', '100%');
	outWin.css('height', '100%');
	outWin.css('z-index', 10);
	outWin.css('display', 'none');
	//outWin.css('background-color', 'black');
	//outWin.css('opacity', '0.6');
	$('body').append(outWin);
	$('body').css('height', '100%');
}



$(document).ready(function()
{
	initOutWin();
})

/*
	@param jqParent: JQuery element that will contain multiple values list
	@param values: list of all possible values
	@param initValues: list of initial values (must be a subset of values)
	
	Before call:
	<span>  (jqParent)
		<select>
			<option>item1</option>
			<option>item2</option>
			<option>item3</option>
		</select>
	</span>
	
	
	After call:
	<span>  (jqParent)
		<input type='text' class='multi_choice' value='' />  (mltInp)
		<div class='multiChoice'>  (jqElem)
			<div class='multiChoiceList'>
				<input type='checkbox'/><span class='choice'>item1</span><br/>
				<input type='checkbox'/><span class='choice'>item2</span><br/>
				<input type='checkbox'/><span class='choice'>item3</span><br/>
			</div>
			<button>Ok</button>
		</div>
	</span>
*/
var multichoice = function(jqParent, values, initValues)
{
	this.values = values;
	this.jqParent = jqParent;
	this.jqElem = null;
	this.mltInp = null;
	this.okBtn = null;
	this.initValues = initValues;
	this.jqList = null;
	
	this.mltClicked = function()
	{
		var obj = this;
		outWin.css('height', document.documentElement.clientHeight);
		outWin.css('width', document.documentElement.clientWidth);
		//alert('height = ' + document.documentElement.clientHeight + '\nwidth = ' + document.documentElement.clientWidth);
		var height = $('body').css('height');
		//outWin.css('height', '100%');
		outWin.click(function(){obj.closePopup();});
		vals = this.mltInp.attr('value').split(',');
		jqParent.find('.multiChoice').find('input').each(function(index, domElem){
			for(var i = 0; i < vals.length; i++)
			{
				val = vals[i];
				if($(domElem).attr('name') == val)
				{
					$(domElem).attr('checked', true);
					return;
				}
			}
			$(domElem).removeAttr('checked');
		});
		outWin.show();
		var width = this.mltInp.css('width');
		//this.jqElem.css('width', width);
		this.jqElem.css('width', 'auto');
		var left = this.mltInp.css('left');
		this.jqElem.css('left', 0);
		var inpHeight = this.mltInp.height();
		this.jqElem.css('top', inpHeight);
		this.jqElem.show();
	}
	
	this.closePopup = function()
	{
		this.jqElem.hide();
		outWin.unbind('click');
		outWin.hide();
	}
	
	this.okBtnClicked = function()
	{
		var text = '';
		this.jqElem.find('input').each(function(index, domElem){
			var chk = $(domElem).attr('checked');
			if(chk)
			{
				if(text != '')
				{
					text += ',';
				}
				text += $(domElem).attr('name');
			}
		});
		this.mltInp.attr('value', text);
		this.mltInp.change();
		
		this.jqElem.hide();
		outWin.unbind('click');
		outWin.hide();
	}
	
	this.getTextInput = function()
	{
		return this.mltInp;
	}
	
	this.init = function()
	{
		var obj = this;  // copy of 'this' for callbacks
		
		this.jqParent.css('position', 'relative');
		var jqSel = this.jqParent.find('select');
		var optionValues = [];
		var n = 0;
		var jqSelOptions = jqSel.find('option').each(function(index, domElem){
			var opt = $(domElem).html();
			if(opt.indexOf('-') != 0)
			{
				optionValues[n] = opt;
				n++;
			}
		});
		this.values = optionValues;
		
		this.mltInp = $('<input type="text" class="multi_choice" value="">');
		jqSel.replaceWith(this.mltInp);
		//this.mltInp = this.jqParent.find('.multi');
		this.mltInp.attr('readonly', 'True');
		this.mltInp.css('background-color', 'yellow');
		this.mltInp.click(function(){obj.mltClicked()});

		this.jqElem = $('<div>');
		this.jqElem.attr('class', 'multiChoice');
		this.jqElem.css('display', 'none');
		this.jqElem.css('position', 'absolute');
		//this.jqElem.css('background-color', '#DDDDDD');
		this.jqElem.css('z-index', 20);
		this.jqList = $('<div></div>');
		this.jqList.css('max-height', '200px');
		this.jqList.css('overflow', 'auto');
		this.jqElem.append(this.jqList);
		
		
		var text = '';
		for(var i = 0; i < this.values.length; i++)
		{
			var inp = $('<input type="checkbox" />');
			inp.attr('name', this.values[i]);
			for(var j = 0; j < this.initValues.length; j++)
			{
				if(this.values[i] == this.initValues[j])
				{
					if(text != '')
					{
						text += ',';
					}
					text += this.initValues[j];
				}
			}
			this.jqList.append(inp);
			var lab = $('<span class="choice"></span>');
			lab.html(this.values[i]);
			this.jqList.append(lab);
			this.jqList.append($('<br>'));
		}
		
		this.mltInp.attr('value', text);
		this.okBtn = $('<button class="button middle_button" style="width: auto">');
		this.okBtn.html('Ok');
		this.jqElem.append(this.okBtn);
		
		this.okBtn.click(function(){obj.okBtnClicked(); return false;});
		
		this.jqParent.append(this.jqElem);
	}
	
	this.init();
}

