/*
Project: META-SHARE prototype implementation
 Author: Salvatore Minutoli <salvatore.minutoli@iit.cnr.it>
*/


var ml_addButtonTempl = '\
	<div class="add">\
		<span  style="display: block; float: left" class="addButton"><img src="add.png"/></span>\
		<span style="display: block; clear: both"></span>\
	</div>\
';

var ml_linesDivTempl = '\
	<div class="lines"></div>\
';

var ml_lineTempl = '\
	<div class="line">\
		<input type="text" name="__a" value="" class="multi_line"></input>\
		<span class="remButton"><img src="delete.png" /></span>\
	</div>\
';

function initMultiLine(opts)
{
	if('addBtnSrc' in opts)
	{
		ml_addButtonTempl = ml_addButtonTempl.replace('add.png', opts.addBtnSrc);
	}
	if('remBtnSrc' in opts)
	{
		ml_lineTempl = ml_lineTempl.replace('delete.png', opts.remBtnSrc);
	}
}

/*
 * @param jqParent: JQuery object in which multiLine object must be added
 * @param initValues: initial values
 * 
 * If jqParent contains children, they will be deleted.
 * 
 *  Before call:
 *  <span> (jqParent)
 *  </span>
 *  
 *  After call:
 *  <span> (jqParent)
 *    <div class='lines'> (jqLinesDiv)
 *      <div class='line'>
 *      	<input type='text' class='multi_line'></input>
 *      	<span class='remButton' />
 *      </div>
 *      <div class='line'/>
 *      <div class='line'/>
 *    </div>
 *    <div class='add'/> (jqAddButtonDiv)
 *  </span>
 *  
 */
var multiLine = function(jqParent, initValues)
{
	this.jqParent = jqParent;
	this.jqLinesDiv = null;
	this.jqAddButtonDiv = null;
	this.linesCount = 0;
	this.lines = [];
	this.initValues = initValues;
	this.currentValue = '';
	this.jqHiddenTextArea = null;
	
	this.createAddButton = function()
	{
		var jqDiv = $(ml_addButtonTempl);
		
		return jqDiv;
	}
	
	this.addLine = function(value)
	{
			var obj = this;
			var line = new singleLine(value);
			this.lines.push(line);
			this.linesCount++;
			var jqLine = line.getLine();
			this.jqLinesDiv.append(jqLine);
			var remButton = line.getRemButton();
			remButton.click(function(){obj.remLine(line);});
			jqLine.change(function(){obj.jqHiddenTextArea.change();});
	}
	
	this.remLine = function(line)
	{
		line.getLine().remove();
		for(var i = 0; i < this.lines.length; i++)
		{
			if(this.lines[i] == line)
			{
				this.lines.splice(i, 1);
				this.linesCount--;
			}
		}
		this.jqHiddenTextArea.change();
	}
	
	this.currentValue = function()
	{
		var text = '';
		
		for(var i = 0; i < this.lines.length; i++)
		{
			var line = this.lines[i];
			if((line != null) && (line != ''))
			{
				var val = line.getCurrentValue();
				if(text != '')
				{
					text += '\n';
				}
				text += val;
			}			
		}
		
		return text;
	}
	
	this.setValue = function(vals)
	{
		if(vals)
		{
			var values = vals.split('\n');
			for(var i = 0; i < values.length; i++)
			{
				var value = values[i];
				if(i >= this.lines.length)
				{
					this.addLine(value);
				}
				else
				{
					this.lines[i].setValue(value);
				}
			}
		}
	}
	
	this.getTextInput = function()
	{
		return this.jqHiddenTextArea;
	}
	
	this.init = function()
	{
		var obj = this;
		this.jqLinesDiv = $(ml_linesDivTempl);
		// Delete elements inside parent
		this.jqParent.html('');
		this.jqHiddenTextArea = $('<textarea style="display: none"></textarea>');
		this.jqParent.append(this.jqHiddenTextArea);
		this.jqParent.append(this.jqLinesDiv);
		this.jqAddButtonDiv = this.createAddButton();
		this.jqAddButtonDiv.find('.addButton').click(function(){obj.addLine();});
		this.jqParent.append(this.jqAddButtonDiv);
		
		var values = this.initValues.split('\n');
		for(var i = 0; i < values.length; i++)
		{
			this.addLine(values[i]);
		}
	}
	
	this.test = function()
	{
		alert(this.currentValue());
	}
	
	this.init();
}

var singleLine = function(initialValue)
{
	this.jqElem = null;
	this.jqRemButton = null;
	this.initialValue = initialValue;
	
	this.getLine = function()
	{
		return this.jqElem;
	}
	
	this.getRemButton = function()
	{
		return this.jqRemButton;
	}
	
	this.getCurrentValue = function()
	{
		var value = this.jqElem.find('input[name="__a"]').attr('value');
		return value;
	}
	
	this.setValue = function(value)
	{
		this.jqElem.find('input[name="__a"]').attr('value', value);
	}
	
	this.init = function()
	{
		this.jqElem = $(ml_lineTempl);
		this.jqElem.find('input[name="__a"]').attr('value', this.initialValue);
		this.jqRemButton = this.jqElem.find('img');
	}
	
	this.init();
}
