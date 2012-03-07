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
							var headerText = a(header).text();
							if(headerText[0] == '_')
							{
								headerText = headerText.replace(/^_/, "");
								a(header).text(headerText);
								a(this).wrapInner("<fieldset class=\"module aligned collapse\"></fieldset>");
							}
						}
					});
			return false;
		})
	}
)(django.jQuery); 
