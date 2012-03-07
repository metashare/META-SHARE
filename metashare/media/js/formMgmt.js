
/*
Project: META-SHARE prototype implementation
 Author: Salvatore Minutoli <salvatore.minutoli@iit.cnr.it>
*/

var d2fsBindings;
var fs2dBindings;
var d2fBindings;
var f2dBindings;
var useDefaultValues = true;

var focusForm = null;

// list of all the forms containing data to be validated
var formArray = [];

// Given the path of data structure returns the Form path 
var bindings;
// Given the path of data structure returns the Formset path
var fsbindings;

var dynFormConds = null;

var rootForm = null;

// Used for tab management
var jqHiddenDiv = null;

var g_saveUrl = null;
var g_valUrl = null;
var g_baseUrl = null;

var g_debug = false;

var g_errorMsgList = [];
var g_jqErrorList = null;
var g_errListMngr = null;

var g_validateTimer = null;

function resetValidateTimeout()
{
	if(g_validateTimer != null)
	{
		clearTimeout(g_validateTimer);
	}
	g_validateTimer = setTimeout("startValidation();", 100);
}

function startValidation()
{
	g_validateTimer = null;
	//console.log("startValidation");
	rootForm.validateBlock(false, true);
}

function getRootForm()
{
	return rootForm;
}

;(function($)
{
	$.fn.manageForms = function(opts)
	{
		var main = $(this);

		jqHiddenDiv = $('<div style="display: none"></div>');
		$('body').append(jqHiddenDiv);
		
		var manager = new formManager(main, opts);
		
		if(g_debug)
		{
			$('#legend').click(function(){manager.showAllForms()})
		}
		
		return false;
	}
})(jQuery);

function isEmpty(obj)
{
   for(var i in obj)
   {
	   return false;
   }
   return true;
}

function subclass(constructor, superConstructor)
{
	function surrogateConstructor()
	{
	}

	surrogateConstructor.prototype = superConstructor.prototype;

	var prototypeObject = new surrogateConstructor();
	prototypeObject.constructor = constructor;

	constructor.prototype = prototypeObject;
}

function formManager(templ, opts)
{
	// ID of HTML object in which this object must be inserted
	this.destId = null;
	// jQuery object in which this object must be inserted
	this.destElem = null;
	// Type of this object: None, Form, FormSet, FormGroup
	this.type = 'None';
	// list of components (1 if type is Formset, 1 or more if type is FormGroup)
	this.componentsName = '';
	// source template for this object. HTML will be copied from this template
	this.templ = templ;
	// Base ID (copied from template)
	this.baseId = this.templ.attr('id');
	// ID assigned to this object
	this.formId = 'fmId_' + this.templ.attr('id');
	// button for adding a Form (if type is FormSet)
	this.addButton;
	// formset name
	this.formsetCompName;
	// jQuery object of this object
	this.jqElem;
	// ID of the object that will contain the Forms (if type is FormSet)
	this.formContainerId;
	// jQuery object that will contain the Forms (if type is FormSet)
	this.formContainer;
	// number of components (if type is FormSet)
	this.compNum = 0;
	// index of this object inside FormSet
	this.compIndex;
	// template for form instances in a formset (form + remButton) (if type is FormSet)
	this.formsetInstance;
	// array of component instances (if type is FormSet or FormGroup)
	this.components = [];
	// DB data associated to the Form
	this.binding = null;
	// flag for empty form (the form is displayed but no data has been loaded into it) (if type is Form or FormGroup)
	this.empty = null;
	// Number of components used, not including empty components (if type is FormSet)
	this.usedCompNum = 0;
	// Form full name (concatenation of parents name + form name)
	this.fullName;
	// ResourceInfo ID (if we are editing an already existing resource)
	this.resId = null;
	// Result of validation ('unknown', 'true', 'false')
	this.validationResult = 'unknown';
	// jQuery object of the template to replicate in formset
	this.jqComp;
	// visibility of this object (due to expanding/collapsing)
	this.visible = true;
	// if this form is mandatory
	this.mandatory = false;
	// true if this is a FormSet that must contain at least one Form
	this.mandatoryFs = false;
	// URL for save
	this.saveUrl = null;
	// URL for validate
	this.valUrl = null;
	// List of fields (if type = 'Form')
	this.fieldInfos = [];
	// role Model
	this.roleModel = null;
	// Does this form depend on the value of a field?
	this.hasCondition = false;
	// Form that contains the field that determines the visibility status of this form
	this.condForm = null;
	// Name of the field that determines the visibility of this form
	this.condFieldName = null;
	// Field that determines the visibility of this form
	this.condField = null;
	// Values of the field for which the form is visible
	this.condFieldValues = null;
	// Has the condition binding been completed? (In case this form is built before the source form)
	this.condProcessed = false;
	// if this form is disabled due to the condition field value
	this.condDisabled = false;
	// True if this FormGroup has tabs
	this.hasTabs = false;
	// tabset object
	this.tabset = null;
	// tabset parent
	this.tabsetParent = null;
	// parent (formManager)
	this.parent = null;
	// true if the FormGroup has been built from a table with no fields
	this.noFields = false;
	// true if this is a role group
	this.roleGroup = false;
	// JQuery object of the Body
	this.jqBodyElem = null;
	
	
	this.fillFormData = function(formDataName, values)
	{
		var res = {};
		
		var names = formDataName.split('/');
		var r = {};
		var name = names[names.length - 1];
		r[name] = values;
		for(var i = names.length - 2; i >= 0; i--)
		{
			name = names[i];
			var rt = {};
			rt[name] = r;
			r = rt;
		}
		
		res = r;
		
		return res;
	}
	
	this.fillFormDataVal = function(formDataName, values)
	{
		var res = {};
		
		var names = formDataName.split('/');
		var r = {};
		var name = names[names.length - 1];
		var name = this.baseId;
		r[name] = values;
		
		res = r;
		
		return res;
	}
	
	this.merge = function(res, val)
	{
		for(var k in val)
		{
			var v = val[k];
			if(res[k])
			{
				if(typeof(val[k]) == 'object')
				{
					if(val[k] instanceof Array)
					{
						var stop = true;
						res[k] = res[k].concat(val[k]);
					}
					else
					{
						this.merge(res[k], val[k]);
					}
				}
				else
				{
					alert('Error in merging data. k = ' + k);
					return;
				}
			}
			else
			{
				res[k] = val[k];
			}
		}
	}
	
	this.createArray = function(formsetDataName, values)
	{
		var res = {};
		var names = formsetDataName.split('/');
		var name = names[names.length - 1];
		res[name] = values;
		for(var i = names.length - 2; i >= 0; i--)
		{
			name = names[i];
			var rt = {};
			rt[name] = res;
			res = rt;
		}
		
		return res;
	}
	
	this.getArrayVal = function(formsetDataName, val)
	{
		var names = formsetDataName.split('/');
		for(var i = 0; i < names.length; i++)
		{
			var name = names[i];
			var arrVal = val[name];
			val = arrVal;
		}
		
		return val;
	}
	
	this.getFieldValues = function()
	{
		var values = {};
		for(var i = 0; i < this.fieldInfos.length; i++)
		{
			var field = this.fieldInfos[i];
			var name = field.getName();
			var value = field.getValue();
			values[name] = value;
		}
		
		return values;
	}
	
	/*
	 * Retrieve data to submit
	 */
	this.getData = function()
	{
		if(this.type == 'Form')
		{
			if(!this.needsValidation(false))
			{
				return null;
			}
			var values = this.getFieldValues();
			var formDataName = f2dBindings[this.fullName];
			//return {type: 'Form', name: this.baseId, values: values};
			var res = this.fillFormData(formDataName, values);
			return res;
		}
		else if(this.type == 'FormGroup')
		{
			var len = this.components.length;
			var values = [];
			var res = {};
			for(var i = 0; i < len; i++)
			{
				var comp = this.components[i];
				var val = comp.getData();
				if(val != null)
				{
					values.push(val);
					this.merge(res, val);
				}
			}
			if(values.length == 0)
			{
				return null;
			}
			return res;
		}
		else if(this.type == 'FormSet')
		{
			if((this.baseId == 'person_distributor_LicenseInfo') || (this.baseId == 'organization_distributor_LicenseInfo'))
			{
				var stop = true;
			}
			if(this.baseId == 'TextInfo_ResourceInfo')
			{
				var stop = true;
			}
			
			var res = [];
			if(this.condDisabled)
			{
				return res;
			}
			var len = this.components.length;
			var formsetDataName = fs2dBindings[this.fullName];
			var values = [];
			for(var i = 0; i < len; i++)
			{
				var comp = this.components[i];
				var val = comp.getData();
				if(val != null)
				{
					if(!isEmpty(val))
					{
						var arrVal = this.getArrayVal(formsetDataName, val);
						values.push(arrVal);
					}
				}
			}
			if(values.length == 0)
			{
				return null;
			}
			res = this.createArray(formsetDataName, values);
			return res;
		}
	}
	
	this.getDataVal = function()
	{
		if(this.type == 'Form')
		{
			//alert('getDataVal: form = ' + this.baseId);
			var values = this.getFieldValues();

			var formDataName = f2dBindings[this.fullName];
			//return {type: 'Form', name: this.baseId, values: values};
			var res = this.fillFormDataVal(formDataName, values);
			//alert('getDataVal: form = ' + this.baseId + ' , returning');
			return res;
		}
	}
	
	this.getValue = function(name, formName)
	{
		if(this.type == 'Form')
		{
			var elem = this.jqElem;
			var field = elem.find('input[name="' + name + '"');
			if(field.length > 0)
			{
				return field.attr('value');
			}
			else
			{
				field = elem.find('select[name="' + name + '"');
				if(field.length > 0)
				{
					return field.attr('value');
				}
				return null;
			}
		}
	}
	
	this.setValue = function(name, formName, keyIndex, value)
	{
		if(this.type == 'Form')
		{
			for(var i = 0; i < this.fieldInfos.length; i++)
			{
				var field = this.fieldInfos[i];
				if(field.getName() == name)
				{
					field.setValue(value);
					return;
				}
			}
			//alert('No field with name ' + name + ' in form ' + this.fullName);
			return;
		}
		else if(this.type == 'FormSet')
		{
			var len = this.components.length;
			var values = [];
			for(var i = 0; i < len; i++)
			{
				var comp = this.components[i];
				comp.setValue(name, formName, keyIndex, value);
			}
		}
		else if(this.type == 'FormGroup')
		{
			var len = this.components.length;
			var values = [];
			for(var i = 0; i < len; i++)
			{
				var comp = this.components[i];
				comp.setValue(name, formName, keyIndex, value);
			}
		}
	}
	
	this.setFields = function(fields, keyIndex, formName)
	{
		if(this.type == 'Form')
		{
			var name = this.templ.attr('id');
			if(formName == name)
			{
				for(var fieldName in fields)
				{
					var fieldValue = fields[fieldName];
					this.setValue(fieldName, formName, keyIndex, fieldValue);
				}
			}
		}
		else if(this.type == 'FormSet')
		{
			var name = this.templ.attr('id');
			var subName = formName.substr(0, name.length);
			if(formName.substr(0, name.length) == name)
			{
				var len = name.length;
				subName = formName.substr(len + 1);
				for(var i = 0; i < this.components.length; i++)
				{
					var comp = this.components[i];
					comp.setFields(fields, keyIndex, subName);
				}
			}
		}
		else if(this.type == 'FormGroup')
		{
			var name = this.templ.attr('id');
			if(formName.substr(0, name.length) == name)
			{
				var subName = formName.substr(name.length + 1);
				for(var i = 0; i < this.components.length; i++)
				{
					var comp = this.components[i];
					comp.setFields(fields, keyIndex, subName);
				}
			}
		}
	}
	
	this.addClicked = function()
	{
		this.addForm();
		return false;
	}
	
	this.remClicked = function(formsetInstance, elem)
	{
		if(this.components.length == 1)
		{
			alert('At least one component must be present');
			return;
		}
		
		var resp = confirm('Delete the selected data?');
		if(resp == true)
		{
			this.remForm(formsetInstance, elem);
		}
	}
	
	this.addForm = function()
	{
		var instance = this.formsetInstance.clone(true);
		var remButton = instance.find('.remButton');
		this.formContainer.append(instance);
		var formInstance = instance.find('.formInstance');
		var elem = new formManager(this.jqComp, {destElem: formInstance, index: this.compNum, parentId: this.formId, parentName: this.fullName, parent: this});
		this.components.push(elem);
		var obj = this;
		remButton.click(function(){
			obj.remClicked(instance, elem);
			return false;
			});
		
		this.compNum++;
	}
	
	this.remForm = function(formsetInstance, elem)
	{
		// Check if the element to remove is the first
		var transfMandatory = false;
		if(elem == this.components[0])
		{
			if(this.mandatoryFs)
			{
				transfMandatory = true;
			}
		}
		
		formsetInstance.remove();
		
		// Elimina l'istanza dall'array di componenti
		for(var i = 0; i < this.components.length; i++)
		{
			if(this.components[i] == elem)
			{
				for(var j = i; j < this.components.length - 1; j++)
				{
					this.components[j] = this.components[j + 1];
					this.components[j].compIndex = j;
					if((j == 0) && transfMandatory)
					{
						this.components[0].setMandatoryMain();
					}
				}
				this.components.length--;
				this.compNum--;
				break;
			}
		}
	}
	
	this.isFormEmpty = function()
	{
		//return this.empty;
		for(var i = 0; i < this.fieldInfos.length; i++)
		{
			var field = this.fieldInfos[i];
			if(!field.isFieldEmpty())
			{
				return false;
			}
		}
		
		return true;
	}
	
	
	 //  Display the data received from the server into the component
	 // and in all children.
	this.displayData4 = function(key, val, level)
	{
		// Temporary to avoid infinite loops
		if(level == 30)
		{
			return;
		}
		
		if(this.type == 'Form')
		{
			var formDataName = f2dBindings[this.fullName];
			if(formDataName.indexOf(key) == 0)
			{
				var f = d2fBindings[key];
				if(f != null)
				{
					var formName = f['form'];
					if(formName == this.fullName)
					{
						var typ = typeof val;
						if(typ == 'object')
						{
							for(var k in val)
							{
								var v = val[k];
								this.setValue(k, null, null, v);
							}
							this.empty = false;
						}
						return;
					}
				}
				if(!(val instanceof Array))
				{
					var typ = typeof val;
					if(typ == 'object')
					{
						for(var k in val)
						{
							var key1;
							if(key == '')
							{
								key1 = k;
							}
							else
							{
								key1 = key + '/' + k;
							}
							var v = val[k];
							this.displayData4(key1, v, level + 1);
						}
					}
				}
			}
		}
		else if(this.type == 'FormSet')
		{
			if((this.baseId == 'person_distributor_LicenseInfo') || (this.baseId == 'organization_distributor_LicenseInfo'))
			{
				var stop = true;
			}
			if(this.baseId == 'TextInfo_ResourceInfo')
			{
				var stop = true;
			}
			var fs = d2fsBindings[key];
			if(fs != null)
			{
				if(this.shouldDisplay(key, val))
				{
					var n = 0;
					for(var i = 0; i < val.length; i++)
					{
						var doAdd = true;
						if(this.roleModel != null)
						{
							var v = val[i];
							if(!(this.roleModel in v))
							{
								doAdd = false;
							}
						}
						if(doAdd)
						{
							if(n == this.compNum)
							{
								this.addForm();
							}
							var v = val[i];
							var comp = this.components[n];
							comp.displayData4(key, v, level + 1);
							n++;
						}
					}
				}
				else
				{
					for(var k in val)
					{
						var key1;
						if(key == '')
						{
							key1 = k;
						}
						else
						{
							key1 = key + '/' + k;
						}
						var v = val[k];
						this.displayData4(key1, v, level + 1);
					}
				}
			}
			else
			{
				if(val instanceof Object)
				{
					for(var k in val)
					{
						var key1;
						if(key == '')
						{
							key1 = k;
						}
						else
						{
							key1 = key + '/' + k;
						}
						var v = val[k];
						this.displayData4(key1, v, level + 1);
					}
				}
			}
		}
		else if(this.type == 'FormGroup')
		{
			for(var i = 0; i < this.components.length; i++)
			{
				var comp = this.components[i];
				comp.displayData4(key, val, level + 1);
			}
		}
	}
	
	this.shouldDisplay = function(key)
	{
		var fs = d2fsBindings[key];
		if(fs != null)
		{
			if(fs instanceof Array)
			{
				for(var i = 0; i < fs.length; i++)
				{
					fsItem = fs[i];
					if(fsItem["form"] == this.fullName)
					{
						return true;
					}
				}
				return false;
			}
			else
			{
				if(fs["form"] == this.fullName)
				{
					return true;
				}
				else
				{
					return false;
				}
			}
		}
	}
	
	
	 // When a validation response is received from the server,
	 // parse it and highlight the errors for each field.
	 
	this.processValidationResponse = function(data)
	{
		var doc = $(data);
		var j = doc.html();
		var ob = JSON.parse(j);
		this.processValidationMessage(ob);
		//alert(j);
	}
	
	this.processValidationMessage = function(ob)
	{
		var isValid = true;
		for(var i = 0; i < this.fieldInfos.length; i++)
		{
			var field = this.fieldInfos[i];
			var name = field.getName();
			if(ob[name])
			{
				isValid = false;
			}
			field.setValidationMsg(ob[name]);
				
		}
		if(isValid)
		{
			this.validationResult = 'true';
			g_errListMngr.remove(this);
		}
		else
		{
			this.validationResult = 'false';
			g_errListMngr.add(this);
		}
		
		return isValid;
	}
	
	// Clear the error messages for this form
	this.clearErrorMessages = function()
	{
		for(var i = 0; i < this.fieldInfos.length; i++)
		{
			var field = this.fieldInfos[i];
			field.setValidationMsg(null);
				
		}
	}
	
	// Clear the error messages for all forms
	this.clearAllErrorMessages = function()
	{
		var forms = this.getAllForms();
		for(var i = 0; i < forms.length; i++)
		{
			var form = forms[i];
			form.clearErrorMessages();
		}
	}
	
	// If this is a form, validate its contents, and highlight the errors, if any.
	// Errors highlighting is performed in the callback 'processValidationResponse'.
	this.validate = function()
	{
		rootForm.validateBlock(false, true);
		return false;
		if(!this.needsValidation())
		{
			this.clearErrorMessages();
			g_errListMngr.remove(this);
			return;
		}
		var a = this.getDataVal();
		var text = JSON.stringify(a);
		//alert('data = ' + text);
		var token = $('html').find('input[name="csrfmiddlewaretoken"]');
		var tokenVal = token.attr('value');
		var postData = {};
		postData['csrfmiddlewaretoken'] = tokenVal;
		postData['form_data'] = text;
		var obj = this;
		$.ajax({type: 'POST', url: g_valUrl, data: postData, success: function(data){obj.processValidationResponse(data);}});
		return false;
	}
	
	/*
	 * Get a list of all forms, collect all form data, and send all data in a single
	 * block to the server. The result of the server will be then split so that each
	 * form will receive its own messages.
	 * @param save: if it is True and validation is Ok, save data on DB
	 */
	this.validateBlock = function(save, silent)
	{
		formArray = this.getValForms();
		if(g_debug)
		{
			console.log('Number of forms = ' + formArray.length);
		}
		var formsData = [];
		for(var i = 0; i < formArray.length; i++)
		{
			var form = formArray[i];
			var data = form.getDataVal();
			var formData = {};
			formData['index'] = i;
			formData['data'] = data;
			formsData[i] = formData;
		}
		var text = JSON.stringify(formsData);
		if(g_debug)
		{
			console.log('data = ' + text);
		}
		var token = $('html').find('input[name="csrfmiddlewaretoken"]');
		var tokenVal = token.attr('value');
		var postData = {};
		postData['csrfmiddlewaretoken'] = tokenVal;
		postData['formsData'] = text;
		//var valUrl = 'http://localhost:8000/validate';
		var obj = this;
		var doSave = save;
		var beSilent = silent;
		$.ajax({type: 'POST', url: this.valUrl, data: postData,
				success: function(data){obj.processValidationResponseBlock(data, doSave, beSilent);},
				error: function(data){alert('The server did not send a correct response')}});
		
		return false;
	}
	
	/*
	 *  receives the responses of all forms validation,
	 *  send each form its own messages
	 *  @param data
	 *  @param save: if it is True and validation id Ok save data on DB
	 */
	this.processValidationResponseBlock = function(data, save, silent)
	{
		if(g_debug)
		{
			console.log(data);
		}
		var doc = $(data);
		var j = doc.html();
		var msgArray = JSON.parse(j);
		var valid = true;
		var formIndex = -1;
		var visLevel = -1;
		g_errListMngr.clear();
		this.clearAllErrorMessages();
		for(var i = 0; i < msgArray.length; i++)
		{
			var msg = msgArray[i];
			var index = msg['index'];
			var err = msg['data'];
			var formMsg = formArray[index];
			var res = formMsg.processValidationMessage(err);
			if(!res)
			{
				valid = false;
				/*
				 * Find the form that needs the fewest tab switches
				 * to be displayed. Possibly no switch at all if the
				 * form is already visible.
				 */
				var numTabs = this.getNumSelectedTabs(formMsg);
				if(numTabs > visLevel)
				{
					visLevel = numTabs;
					formIndex = i;
				}
				/*
				if(formIndex == -1)
				{
					formIndex = i;
				}
				*/
			}
		}
		
		if(valid)
		{
			if(save == false)
			{
				if(!silent)
				{
					alert('Validation OK');
				}
			}
			if(save == true)
			{
				this.submitData();
			}
		}
		else
		{
			if(!silent)
			{
				alert('Validation failed');
			}
			/*
			 * Open the tab that contains a form
			 * containing an error.
			 */
			if(save == true)
			{
				var form = formArray[formIndex];
				this.displayForm(form);
			}
		}
	}
	
	/*
	 * Determine how many tabs are already selected for form
	 */
	this.getNumSelectedTabs = function(form)
	{
		var num = 0;
		var tabList = form.getTabsets();
		if(tabList.length > 0)
		{
			for(var i = 0; i < tabList.length; i++)
			{
				var elem = tabList[i];
				var tabset = elem[0];
				var tabIndex = elem[1];
				if(tabset.currentTab == tabIndex)
				{
					num++;
				}
				else
				{
					break;
				}
			}
		}
		
		return num;
	}
	
	/*
	 * Select the tabs needed to make form visible.
	 */
	this.displayForm = function(form)
	{
		var tabList = form.getTabsets();
		if(tabList.length > 0)
		{
			for(var i = 0; i < tabList.length; i++)
			{
				var elem = tabList[i];
				var tabset = elem[0];
				var tabIndex = elem[1];
				var tab = tabset.tabItems[tabIndex];
				tabset.tabSelected(tab);
			}
		}
	}
	
	/*
	 * Get all forms
	 */
	this.getAllForms = function()
	{
		if(this.type == 'Form')
		{
			var forms = [];
			forms[0] = this;
			return forms;
		}
		else if((this.type == 'FormSet') || (this.type == 'FormGroup'))
		{
			var forms = [];
			for(var i = 0; i < this.components.length; i++)
			{
				var sub = this.components[i].getAllForms();
				
				// cfedermann: added check to ensure that a form for this
				//             component could be found; if not, continue.
				if (!sub) {
				    continue;
				}
				
				for(var k = 0; k < sub.length; k++)
				{
					var ind = forms.length;
					forms[ind] = sub[k];
				}
			}
			
			return forms;
		}
	}
	
	/*
	 * Get all formsets
	 */
	this.getAllFormsets = function()
	{
		var formsets = [];
		if(this.type == 'Form')
		{
			return formsets;
		}
		
		if(this.type == 'FormSet')
		{
			formsets[0] = this;
		}
		
		for(var i = 0; i < this.components.length; i++)
		{
			var comp = this.components[i];
			var sub = comp.getAllFormsets();
			for(var k = 0; k < sub.length; k++)
			{
				var ind = formsets.length;
				formsets[ind] = sub[k];
			}
		}
		
		return formsets;
	}
	
	/*
	 * Get all formgroups
	 */
	this.getAllFormgroups = function()
	{
		var formgroups = [];
		if(this.type == 'Form')
		{
			return formgroups;
		}
		
		if(this.type == 'FormGroup')
		{
			formgroups[0] = this;
		}
		
		for(var i = 0; i < this.components.length; i++)
		{
			var comp = this.components[i];
			var sub = comp.getAllFormgroups();
			for(var k = 0; k < sub.length; k++)
			{
				var ind = formgroups.length;
				formgroups[ind] = sub[k];
			}
		}
		
		return formgroups;
	}
	
	/*
	 * returns true if this form must be validated.
	 * if noRec is true do not check the parent. 
	 */
	this.needsValidation = function(noRec)
	{
		if(this == rootForm)
		{
			return true;
		}
		
		if(this.type == 'Form')
		{
			if(this.condDisabled)
			{
				return false;
			}
			if(!this.isFormEmpty())
			{
				return true;
			}
			if(this.mandatory)
			{
				if(noRec)
				{
					return true;
				}
				else
				{
					// Check that the forms that have a reference for this are also mandatory
					return this.parent.needsValidation(false);
				}
			}
			else
			{
				//return false;
				var res = false;
				if(this.compIndex == 0)
				{
					if((this.parent != rootForm) && (this.parent.type == 'FormGroup'))
					{
						res = this.parent.containsData();
					}
				}
				return res;
			}
		}
		else if(this.type == 'FormGroup')
		{
			// The first form has a reference for the others
			if(this.containsData())
			{
				return true;
			}
			var res = false;
			if(this.noFields == false)
			{
				res = this.components[0].needsValidation(true);
			}
			if(res)
			{
				return this.parent.needsValidation(false);
			}
			else
			{
				return false;
			}
		}
		else if(this.type == 'FormSet')
		{
			return this.parent.needsValidation(false);
		}
		
	}
	
	/*
	 * Check if some table in the subtree contains data.
	 */
	this.containsData = function()
	{
		if(this.type == 'Form')
		{
			if(this.condDisabled)
			{
				return false;
			}
			return (!this.isFormEmpty());
		}
		else if((this.type == 'FormGroup') || (this.type == 'FormSet'))
		{
			var res = false;
			for(var i = 0; i < this.components.length; i++)
			{
				var f = this.components[i];
				if(f.containsData())
				{
					return true;
				}
			}
			return res;
		}
	}
	
	/*
	 * Get all forms that need validation.
	 * Mandatory forms and non empty forms.
	 */
	this.getValForms = function()
	{
		var forms = this.getAllForms();
		var retForms = [];
		var n = 0;
		for(var i = 0; i < forms.length; i++)
		{
			var form = forms[i];
			if(form.needsValidation(false))
			{
				retForms[n] = forms[i];
				n++;
			}
			continue;
			if(form.condDisabled)
			{
				continue;
			}
			if(form.mandatory)
			{
				retForms[n] = forms[i];
				n++;
			}
			else
			{
				if(!form.empty)
				{
					retForms[n] = forms[i];
					n++;
				}
			}
		}
		
		return retForms;
	}
	
	this.setMandatory = function()
	{
		if(this.type != 'Form')
		{
			var msg = 'setMandatory should only be used for a Form\n';
			msg += 'Current object is ' + this.type + ' (' + this.fullName + ')'; 
			alert(msg);
			return;
		}
		var dataPath = f2dBindings[this.fullName];
		this.mandatory = d2fBindings[dataPath]['mandatory'];
	}
	
	this.setMandatoryFs = function()
	{
		var dataPath = fs2dBindings[this.fullName];
		this.mandatoryFs = this.isMandatoryTab();
	}
	
	// set the mandatory flag to true for the first form
	this.setMandatoryMain = function()
	{
		if(this.type == 'Form')
		{
			this.setMandatory();
		}
		else if(this.type == 'FormGroup')
		{
			if(this.noFields == false)
			{
				this.components[0].setMandatory();
			}
		}
	}
	
	this.isMandatoryTab = function()
	{
		if(this.type == 'Form')
		{
			return this.mandatory;
		}
		
		if(this.type == 'FormGroup')
		{
			if(this.noFields)
			{
				return false;
			}
			else
			{
				return this.components[0].mandatory;
			}
		}
		
		if(this.type == 'FormSet')
		{
			return this.components[0].isMandatoryTab();
		}
	}
	
	this.submitData = function()
	{
		if(g_debug)
		{
			console.log('Submitting data');
		}
		var a = this.getData();
		var token = $('html').find('input[name="csrfmiddlewaretoken"]');
		var tokenVal = token.attr('value');
		var text = JSON.stringify(a);
		var postData = {};
		postData['csrfmiddlewaretoken'] = tokenVal;
		postData['form_data'] = text;
		//alert('Checking for resId in ' + obj.fullName);
		if(this.resId != null)
		{
			//alert('resId = ' + obj.resId);
			postData['resId'] = this.resId;
		}
		$.ajax({type: 'POST', url: this.saveUrl, data: postData,
			success: function(data){
				var jqData = $(data);
				if (jqData.is('#saveResponse'))
				{
					var msg = jqData.html();
					alert(msg);
				}
				else
				{
					document.open();
					document.write(data);
					document.close();
				}
			},
			error: function(data){
				alert('The server did not send a correct response.');
			}
		});
		return false;
	}
	
	// returns the field with the given name
	this.getFieldInfo = function(name)
	{
		for(var i = 0; i < this.fieldInfos.length; i++)
		{
			if(this.fieldInfos[i].getName() == name)
			{
				return this.fieldInfos[i];
			}
		}
		
		return null;
	}
	
	/*
	 *  This function searches the form that contains the values
	 *  for the given data path.
	 */
	this.getFormByDataPath = function(dataPath)
	{
		var forms = rootForm.getAllForms();
		for(var i = 0; i < forms.length; i++)
		{
			var form = forms[i];
			var formDataPath = f2dBindings[form.fullName];
			if(formDataPath == dataPath)
			{
				return form;
			}
		}
		return null;
	}
	
	/*
	 *  This function will be called when the field, on which
	 *  this form depends, changes.
	 */
	this.condFieldChanged = function(fieldInfo)
	{
		var fieldValue = fieldInfo.getValue();
		var values = this.condFieldValues.split(',');
		
		resetValidateTimeout();
		for(var i = 0; i < values.length; i++)
		{
			var value = values[i];
			if(fieldValue == value)
			{
				//alert('Form ' + this.baseId + ' enabled');
				if((this.type == 'FormGroup') && (this.hasTabs))
				{
					this.tabset.jqElem.show();
				}
				else if(((this.type == 'Form') || (this.type == 'FormSet') || (this.type == 'FormGroup')) && (this.parent.hasTabs))
				{
					this.jqBodyElem.show();
				}
				else
				{
					this.jqElem.show();
				}
				this.condDisabled = false;
				return;
			}
		}
		//alert('Form ' + this.baseId + ' disabled');
		if((this.type == 'FormGroup') && (this.hasTabs))
		{
			this.tabset.jqElem.hide();
		}
		else if(((this.type == 'Form') || (this.type == 'FormSet') || (this.type == 'FormGroup')) && (this.parent.hasTabs))
		{
			this.jqBodyElem.hide();
		}
		else
		{
			this.jqElem.hide();
		}
		this.condDisabled = true;
	}
	
	/*
	 *  This function triggers the check on condition field.
	 */
	this.checkCondition = function()
	{
		if(this.hasCondition)
		{
			var fieldInfo = this.condField;
			if(fieldInfo)
			{
				this.condFieldChanged(fieldInfo);
			}
		}
	}
	
	/*
	 *  This function checks if this form visibility depends on the contents
	 *  of a field in some other form.
	 */
	this.processConditions = function()
	{
		if(!this.condProcessed)
		{
			if(dynFormConds)
			{
				var dataPath = null;
				if(this.type == 'Form')
				{
					dataPath = f2dBindings[this.fullName];
				}
				else if(this.type == 'FormGroup')
				{
					dataPath = this.fullName;
				}
				else if(this.type == 'FormSet')
				{
					dataPath = fs2dBindings[this.fullName];
				}
				for(var i = 0; i < dynFormConds.length; i++)
				{
					var cond = dynFormConds[i];
					for(var trgtFormDataPath in cond)
					{
						if((trgtFormDataPath == dataPath) || (dataPath.indexOf(trgtFormDataPath) == 0))
						{
							this.hasCondition = true;
							var srcFormDataPath = cond[trgtFormDataPath]['form'];
							var condFieldName = cond[trgtFormDataPath]['field'];
							var condFieldValues = cond[trgtFormDataPath]['values'];
							var srcForm = rootForm.getFormByDataPath(srcFormDataPath);
							if(srcForm)
							{
								this.condForm = srcForm;
								this.condFieldName = condFieldName;
								this.condFieldValues = condFieldValues;
								// Bind the 'condFieldChanged' function to the 'change' event on the field
								var obj = this;
								var fieldInfo = this.condForm.getFieldInfo(this.condFieldName);
								this.condField = fieldInfo;
								fieldInfo.jqInput.change(function(){
									obj.condFieldChanged(fieldInfo);
								});
								this.condProcessed = true;
							}
							else
							{
								this.condProcessed = false;
							}
							return;
						}
					}
				}
				this.hasCondition = false;
			}
			this.condProcessed = true;
		}
	}
	
	// returns a list of all the tabset ancestors that are parent of this
	this.getTabsets = function()
	{
		var tabList = [];

		if(this.parent != null)
		{
			tabList = this.parent.getTabsets();
		}

		if(this.parent != null)
		{
			if(this.parent.tabset != null)
			{
				tabList[tabList.length] = [this.parent.tabset, this.compIndex];
			}
		}
		
		return tabList;
		
	}
	
	this.getParentTable = function()
	{
		if(this.type == 'Form')
		{
			if(this.parent.type == 'FormGroup')
			{
				if(this.compIndex > 0)
				{
					if(this.parent.noFields == false)
					{
						return this.parent.components[0];
					}
					else
					{
						return this.parent;
					}
				}
			}
		}
		else if(this.type == 'FormGroup')
		{
			if(this.compIndex > 0)
			{
				if(this.parent.noFields == false)
				{
					return this.parent.components[0];
				}
				else
				{
					return this.parent;
				}
			}
			else
			{
				if(this.parent == null)
				{
					return null;
				}
			}
		}
		else if(this.type == 'FormSet')
		{
			if(!this.roleModel)
			{
				if(this.parent.type == 'FormGroup')
				{
					if(this.compIndex > 0)
					{
						if(this.parent.noFields == false)
						{
							return this.parent.components[0];
						}
						else
						{
							return this.parent;
						}
					}
				}
			}
		}
		
		return this.parent.getParentTable();
	}
	
	this.showAllForms = function()
	{
		var forms = this.getAllForms();
		var msg = '';
		for(var i = 0; i < forms.length; i++)
		{
			var f = forms[i];
			msg += f.fullName + '\n';
			var p = f.getParentTable();
			var parentName = null;
			if(p)
			{
				parentName = f.getParentTable().fullName;
			}
			else
			{
				parentName = 'ResourceInfo';
			}
			msg += '  ' + parentName + '\n';
		}
		console.log(msg);
	}
	
	this.checkStatus = function()
	{
		if(this.type == 'Form')
		{
			var msg = '';
			msg += 'Form: ' + this.baseId + '\n';
			msg += 'fullName: ' + this.fullName + '\n';
			msg += 'mandatory: ' + this.mandatory + '\n';
			var parentName = null;
			var containsData = false;
			p = this.getParentTable();
			if(p)
			{
				parentName = p.fullName;
				containsData = p.containsData();
			}
			else
			{
				parentName = 'ResourceInfo';
				containsData = true;
			}
			msg += 'parentTable: ' + parentName + '\n';
			msg += 'containsData: ' + containsData + '\n';
			console.log(msg);
		}
	}
	
	this.init = function()
	{
		if('debug' in opts)
		{
			g_debug = opts.debug;
		}
		
		if('errorMessages' in opts)
		{
			var jqElem = $('#' + opts.errorMessages);
			if(jqElem && (jqElem.length > 0))
			{
				g_errListMngr = new errListManager(jqElem);
			}
			else
			{
				alert('Invalid errorMessages ID');
			}
		}
		if('bindings' in opts)
		{
			
			var b = $('#' + opts.bindings).html();
			bindings = JSON.parse(b);
			d2fBindings = bindings;
			f2dBindings = {};
			for(var k in d2fBindings)
			{
				var f = d2fBindings[k]["form"];
				f2dBindings[f] = k;
			}
			
			var fsb = $('#' + opts.fsbindings).html();
			fsbindings = JSON.parse(fsb);
			d2fsBindings = fsbindings;
			fs2dBindings = {};
			for(var k in d2fsBindings)
			{
				var f = d2fsBindings[k]["form"];
				var f = d2fsBindings[k];
				if(f instanceof Array)
				{
					for(var i = 0; i < f.length; i++)
					{
						fs = f[i]["form"];
						fs2dBindings[fs] = k;
					}
				}
				else
				{
					f = f["form"];
					fs2dBindings[f] = k;
				}
			}
			
			
		}
		
		if('index' in opts)
		{
			this.compIndex = opts.index;
		}
		
		if('parent' in opts)
		{
			this.parent = opts.parent;
		}
		
		if('parentName' in opts)
		{
			this.fullName = opts.parentName + "/";
		}
		else
		{
			this.fullName = "";
		}
		this.fullName += this.templ.attr('id');
		
		if('testButtonId' in opts)
		{
			var obj = this;
			$('#' + opts.testButtonId).click(function(){
				obj.validateBlock(false, false);
				return false;
			});
			
			//alert('Checking for  resId');
			$('body').find('#resId').each(function(index, domElem){
				obj.resId = $(domElem).html();
				//alert('resId set to ' + obj.resId + ' in ' + obj.fullName);
				})
		}
		
		if('useDefaultValues' in opts)
		{
			useDefaultValues = opts.useDefaultValues;
		}
		
		if('submitButtonId' in opts)
		{
			var obj = this;
			$('#' + opts.submitButtonId).click(function(){
				obj.validateBlock(true, false);
				//obj.submitData();
				return false;
			});
		}
		
		if('baseUrl' in opts)
		{
			g_baseUrl = opts.baseUrl;
		}
		
		if('saveUrl' in opts)
		{
			this.saveUrl = opts.saveUrl;
			g_saveUrl = opts.saveUrl;
		}
		
		if('valUrl' in opts)
		{
			this.valUrl = opts.valUrl;
			g_valUrl = opts.valUrl;
		}
		
		if('destId' in opts)
		{
			this.destId = opts.destId;
			this.destElem = $('#' + this.destId);
		}
		else if('destElem' in opts)
		{
			this.destElem = opts.destElem;
		}
		else
		{
			alert('Error: no destination provided.');
			return false;
		}
		
		if('parentId' in opts)
		{
			this.formId = opts.parentId + '_' + this.baseId;
		}
		
		if('index' in opts)
		{
			this.compIndex = opts.index;
			this.formId += '_' + opts.index;
		}
		
		if('dynFormConds' in opts)
		{
			var text = $('#' + opts.dynFormConds).html();
			dynFormConds = JSON.parse(text);
		}

		if(this.templ.hasClass('formgroup'))
		{
			this.type = 'FormGroup';
			//var a = $('<div id = "' + this.formId + '" class="formgroup"></div>');
			var a = this.templ.clone(true).removeAttr('def').removeAttr('id').attr('id', this.formId);
			var header = a.find('.formgroupHeader');
			var body = a.find('.formgroupBody'); 
			if(header.length > 0)
			{
				if(body.length > 0)
				{
					//header.find('.formGroupName').click(function(){body.toggle()});
				}
			}
			
			if(this.templ.hasClass('tabbed') || this.templ.hasClass('tabbedComp'))
			{
				this.hasTabs = true;
			}
			
			this.jqElem = a;
			this.destElem.append(a);
			this.componentsName = this.templ.attr('def').split(' ');
			for(var i = 0; i < this.componentsName.length; i++)
			{
				var comp = this.componentsName[i];
				var compElem = $('#' + comp);
				var elem;
				if(body.length > 0)
				{
					elem = new formManager($(compElem), {destElem: body, parentId: this.formId, parentName: this.fullName, parent: this, index: i});
				}
				else
				{
					elem = new formManager($(compElem), {destId: this.formId, parentId: this.formId, parentName: this.fullName, parent: this, index: i});
				}
				this.components.push(elem);
			}
			
			this.jqBodyElem = this.jqElem.find('.formgroupBody').first();

			if(this.templ.hasClass('noFields'))
			{
				this.noFields = true;
			}
			
			if(this.templ.hasClass('tabbed'))
			{
				this.tabsetParent = this.jqElem.parent();
				this.jqElem.detach().appendTo(jqHiddenDiv);
				this.tabset = new tabSet(this.jqElem, this, this.tabsetParent);
			}
			
			if(this.templ.hasClass('tabbedComp'))
			{
				var templ = '\
					<div class="formgroup dummy">\
						<div class="formgroupHeader">\
							<span class="formGroupName"></span>\
						</div>\
						<div class="formgroupBody">\
						</div>\
					</div>\
					';
				var jqTempl = $(templ);
				var jqTemplHeader = jqTempl.find('.formgroupHeader');
				var jqTemplBody = jqTempl.find('.formgroupBody');
				var jqTemplName = jqTempl.find('.formGroupName');
				this.jqElem.after(jqTempl);
				this.jqElem.detach().appendTo(jqTemplBody);
				this.tabsetParent = jqTemplBody;
				jqTemplName.html(this.baseId);
				this.jqElem.detach().appendTo(jqHiddenDiv);
				this.tabset = new tabSet(this.jqElem, this, this.tabsetParent);
			}
			
			if(this.templ.hasClass('roleGroup'))
			{
				this.roleGroup = true;
			}
			
			if(rootForm)
			{
				this.processConditions();
				this.checkCondition();
			}
		}
		else if(this.templ.hasClass('formset'))
		{
			var obj = this;
			this.type = 'FormSet';
			var a = $('#' + this.templ.attr('id')).clone(true).removeAttr('id').attr('id', this.formId);
			this.formsetButton = a.find('.formsetButton');
			if(this.formsetButton)
			{
				var img = $('<img>');
				img.attr('src', g_baseUrl + '/site_media/css/sexybuttons/images/icons/silk/section_expanded.png');
				this.formsetButton.append(img);
				this.formsetButton.click(function(){
					if(obj.visible)
					{
						obj.jqElem.children().filter('.formsetBody').hide();
						obj.formsetButton.children().filter('img').attr('src', g_baseUrl + '/site_media/css/sexybuttons/images/icons/silk/section_collapsed.png')
						obj.visible = false;
					}
					else
					{
						obj.jqElem.children().filter('.formsetBody').show();
						obj.formsetButton.children().filter('img').attr('src', g_baseUrl + '/site_media/css/sexybuttons/images/icons/silk/section_expanded.png')
						obj.visible = true;
					}
					return false;
				})
			}
			this.destElem.append(a);
			this.jqElem = a;
			this.formContainerId = this.formId + '_container';
			this.formContainer = a.find('.formContainer').attr('id', this.formContainerId);
			// save a copy of formsetInstance
			this.formsetInstance = this.formContainer.find('.formsetInstance').clone(true);
			// remove the current formsetInstance (it will be added every time a new form is added)
			var remInstance = this.formContainer.find('.formsetInstance');
			remInstance.remove();
			
			this.jqBodyElem = this.jqElem.find('.formsetBody').first();

			var role = this.templ.attr('role');
			if(role)
			{
				this.roleModel = role;
			}
			this.formsetCompName = this.templ.attr('def');
			this.jqComp = $('#' + this.formsetCompName);
			this.addButton = a.find('.addButton').attr('id', this.formId + '_addButton');
			this.addForm();
			this.addButton.click(function(){
				obj.addClicked();
				return false;
				});
			
			if(rootForm)
			{
				this.processConditions();
				this.checkCondition();
			}
			
		}
		else if(this.templ.hasClass('form'))
		{
			this.type = 'Form';
			this.empty = true;
			var a = $('#' + this.templ.attr('id')).clone(true).removeAttr('id').attr('id', this.formId);
			var header = a.find('.formHeader');
			var body = a.find('.formBody'); 
			if(header.length > 0)
			{
				if(body.length > 0)
				{
					//header.find('.formName').click(function(){body.toggle()});
					if(g_debug)
					{
						var objThis = this;
						header.find('.formName').click(function(){objThis.checkStatus()});
					}
				}
			}

			this.jqElem = a;
			var obj = this;
			a.find('.fieldInfo').each(function(index, domElem){
				obj.fieldInfos[index] = new  fieldInfo($(domElem), obj, useDefaultValues);
			});
			this.jqBodyElem = this.jqElem.find('.formBody').first();
			
			if(rootForm)
			{
				this.processConditions();
				this.checkCondition();
				this.setMandatory();
			}
			
			this.destElem.append(a);
		}

		if('dbDataId' in opts)
		{
			// This code should be run only by the root form
			
			var text = $('#' + opts.dbDataId).html();
			text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
			var dbData = JSON.parse(text);
			this.displayData4("", dbData, 0);
			
			rootForm = this;
			
			var forms = this.getAllForms();
			for(var i = 0; i < forms.length; i++)
			{
				var form = forms[i];
				form.setMandatory();
				form.processConditions();
				form.checkCondition();
			}
			
			var formsets = this.getAllFormsets();
			for(var i = 0; i < formsets.length; i++)
			{
				var formset = formsets[i];
				formset.processConditions();
				formset.checkCondition();
				formset.setMandatoryFs();
			}
			
			var formgroups = this.getAllFormgroups();
			for(var i = 0; i < formgroups.length; i++)
			{
				var formgroup = formgroups[i];
				formgroup.processConditions();
				formgroup.checkCondition();
			}
			
		}
		
		if((this == rootForm) && (this.tabset != null))
		{
			// Highlight mandatory tabs
			for(var i = 0; i < this.components.length; i++)
			{
				var comp = this.components[i];
				if(comp.isMandatoryTab() == true)
				{
					// Highlight tab
					this.tabset.highlightTab(i);
				}
			}
		}
	}
	
	this.init();
	
}

/*
 * fieldInfo
 * @param jqElem: JQuery object associated with this object
 * @param form: formManager object of the form this field belongs to
 * @param useDefaultValues: if false remove default value form input
 */
function fieldInfo(jqElem, form, useDefaultValues)
{
	// JQuery object
	this.jqElem = jqElem;
	// form this field belongs to
	this.form = form;
	// flag for multiline fields
	this.isMultiLine = false;
	// multiline object, if isMultiLine
	this.mltLine = null;
	// flag for multichoice fields
	this.isMultiChoice = false;
	// multichoice object, if isMultiChoice
	this.mltChoice = null;
	// name of the field
	this.fieldName = null;
	// JQuery element form input field
	this.jqInput = null;
	// input type (input(type=text), select, textarea, checkbox)
	this.inputType = null;
	// if false remove default value form input
	this.useDefaultValues = useDefaultValues;
	// JQuery element for error messages
	this.jqErrorMsg = null;
	// flag for NullBoolean fields
	this.isNullBoolean = null;
	
	
	// returns the name of the field
	this.getName = function()
	{
		return this.fieldName;
	}
	
	this.getValue = function()
	{
		var value = this.jqInput.attr('value');
		if(this.inputType == 'checkbox')
		{
			if(this.jqInput.attr('checked'))
			{
				value = true;
			}
			else
			{
				value = false;
			}
		}
		else if(this.isMultiChoice)
		{
			value = value.replace(/,/g, '\n');
		}
		else if(this.isMultiLine)
		{
			value = this.mltLine.currentValue();
		}
		else if(this.isNullBoolean)
		{
			if(value == 'True')
			{
				value = true;
			}
			else if(value == 'False')
			{
				value = false;
			}
			else
			{
				value = null;
			}
		}
		
		return value;
	}
	
	this.setValue = function(value)
	{
		if(this.isMultiLine)
		{
			this.mltLine.setValue(value);
			return;
		}
		if(this.inputType == 'checkbox')
		{
			if(value == true)
			{
				this.jqInput.checked = true;
				this.jqInput.attr('checked', true);
			}
			else
			{
				this.jqInput.checked = false;
				this.jqInput.attr('checked', false);
			}
		}
		else
		{
			if(this.isMultiChoice)
			{
				value = value.replace(/\n/g, ',');
			}
			if(this.isNullBoolean)
			{
				if(value == true)
				{
					value = 'True';
				}
				else if(value == false)
				{
					value = 'False';
				}
				else
				{
					value = 'None';
				}
			}
			this.jqInput.attr('value', value);
		}
	}
	
	this.setValidationMsg = function(msgList)
	{
		var errMsgs = '';
		if(msgList)
		{
			for(var i = 0; i < msgList.length; i++)
			{
				var msg = msgList[i];
				if(errMsgs != '')
				{
					errMsgs += ', ';
				}
				errMsgs += msg;
			}
		}
		this.jqErrorMsg.html(errMsgs);
	}
	
	this.isFieldEmpty = function()
	{
		var value = this.jqInput.attr('value');
		if(this.inputType == 'checkbox')
		{
			return false;
		}
		else if(this.isMultiLine)
		{
			value = this.mltLine.currentValue();
		}
		else if(this.isNullBoolean)
		{
			if((value == 'True') || (value == 'False'))
			{
				return false;
			}
			else
			{
				return true;
			}
		}
		
		return ((value == null) || (value == ''));
	}
	
	this.init = function()
	{
		var formObj = this.form;
		this.fieldName = this.jqElem.attr('fieldName');
		this.jqInput = this.jqElem.find('input, textarea, select, checkbox');
		if(this.jqInput.is('input'))
		{
			if(this.jqInput.attr('type') == 'text')
			{
				this.inputType = 'text';
			}
			else if(this.jqInput.attr('type') == 'checkbox')
			{
				this.inputType = 'checkbox';
				//this.jqInput.removeAttr('value');
			}
			else
			{
				alert('Unknown input type');
			}
		}
		else if(this.jqInput.is('textarea'))
		{
			this.inputType = 'textarea';
		}
		else if(this.jqInput.is('select'))
		{
			this.inputType = 'select';
		}
		else
		{
			alert('Unknown input tag');
		}
		
		this.jqErrorMsg = this.jqElem.find('.errors');
		
		var obj = this;
		this.jqElem.find('span.widget.multi_values.CharField').each(function(index, domElem){
			var mcl = $(domElem).find('select.multi_choice_list');
			if(mcl.length > 0)
			{
				var mChoice = new multichoice($(domElem), '', '');
				obj.isMultiChoice = true;
				obj.mltChoice = mChoice;
				obj.jqInput = obj.mltChoice.getTextInput();
				//alert('MultiChoice field: ' + obj.fieldName);
			}
			else
			{
				var mLine = new multiLine($(domElem), '');
				obj.isMultiLine = true;
				obj.mltLine = mLine;
				obj.jqInput = obj.mltLine.getTextInput();
				//alert('MultiChoice field: ' + obj.fieldName);
			}
		});
		
		this.jqElem.find('span.widget.multi_values.URLField, span.widget.multi_values.EmailField').each(function(index, domElem){
			var mcl = $(domElem).find('select.multi_choice_list');
			if(mcl.length == 0)
			{
				var mLine = new multiLine($(domElem), '');
				obj.isMultiLine = true;
				obj.mltLine = mLine;
				obj.jqInput = obj.mltLine.getTextInput();
				//alert('MultiChoice field: ' + obj.fieldName);
			}
		});
		
		this.jqElem.find('span.widget.nullBoolean').each(function(index, domElem){
			obj.isNullBoolean = true;
		});
		
		/*
		this.jqElem.find('span.widget.DateField > input').each(function(index, domElem){
			$(domElem).datepicker({dateFormat: 'yyyy-mm-dd'});
		});
		*/

		if(!this.useDefaultValues)
		{
			this.jqInput.attr('value', '');
		}
		this.jqInput.blur(function(){
			return false;
		});
		this.jqInput.change(function(){
			formObj.empty = false;
			formObj.validate();
			return false;
		});
		this.jqInput.focus(function(){
			focusForm = formObj;
			return false;
		});
	}
	
	this.init();
}

function errListManager(jqMessageBlock)
{
	this.jqMessageBlock = jqMessageBlock;
	this.forms = [];
	this.jqErrList = null;
	this.jqTitle = null;
	this.title = "These forms contain missing or incorrect data. Click to display the form.";
	this.lineTempl = "<div class='formError'></div>"
	
	this.add = function(form)
	{
		for(var i = 0; i < this.forms.length; i++)
		{
			if(this.forms[i] == form)
			{
				return;
			}
		}
		
		this.forms[this.forms.length] = form;
		this.updateDisplay();
	}
	
	this.remove = function(form)
	{
		for(var i = 0; i < this.forms.length; i++)
		{
			if(this.forms[i] == form)
			{
				this.forms.splice(i, 1);
				this.updateDisplay();
			}
		}
	}
	
	this.clear = function()
	{
		this.forms = [];
		this.updateDisplay();
	}
	
	this.updateDisplay = function()
	{
		this.jqErrList.html('');
		
		if(this.forms.length <= 0)
		{
			this.jqTitle.hide();
			this.jqErrList.hide();
		}
		else
		{
			this.jqTitle.show();
			this.jqErrList.show();
		}
		
		for(var i = 0; i < this.forms.length; i++)
		{
			var jqLine = $(this.lineTempl);
			jqLine.attr('index', i);
			//var text = this.forms[i].fullName;
			var text = this.forms[i].baseId;
			jqLine.html(text);
			var objThis = this;
			var index = i;
			jqLine.click(function(event){objThis.lineClicked(event.target);});
			this.jqErrList.append(jqLine);
		}
	}
	
	this.lineClicked = function(domElem)
	{
		var index = -1;
		index = $(domElem).attr('index');
		//alert('index = ' + index);
		if((index >= 0) && (index < this.forms.length))
		{
			rootForm.displayForm(this.forms[index]);
		}
	}
	
	this.init = function()
	{
		this.jqTitle = $('<div></div>');
		this.jqTitle.html(this.title);
		this.jqMessageBlock.append(this.jqTitle);
		this.jqErrList = $('<div id="errList"></div>')
		this.jqMessageBlock.append(this.jqErrList);
		this.updateDisplay();
	}
	
	this.init();
}

