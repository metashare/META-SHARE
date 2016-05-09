// addCollapseToAllStackedInlines.js

(
	function(a)
	{
		a(document).ready(function()
		{
			//a("div.inline-group").wrapInner("<fieldset class=\"module aligned collapse\"></fieldset>");
			a("div.inline-group").each(function(index)
					{
						var header = a(this).find('h2').get(0);
						if(header)
						{
							var headerTitle = a(header).find('.formset_title').get(0);
							var headerText = a(headerTitle).text();
							if(headerText[0] == '_')
							{
								headerText = headerText.replace(/^_/, "");
								a(headerTitle).text(headerText);
								a(this).wrapInner("<fieldset class=\"module aligned collapse\"></fieldset>");
							}
						}
					});
			return false;
		})
	}
)(django.jQuery); 
