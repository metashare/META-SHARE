
var newwin = null;
var helpWinName = "Help";

function showHelp(event)
{
	if(newwin != null)
	{
		newwin.close();
		newwin = null;
	}
	
	var url = $(event.target).attr('kblink');
	if(!url)
	{
		/*
		 * From 'admin/edit_inline/stacked.html
		 */
		var base = $(event.target).attr('kbbase');
		var compName = $(event.target).attr('kbcomp');
		if(!base || !compName)
		{
			return false;
		}
		compName = compName.replace(/^_/, "");
		compName = compName.replace(/s$/, "");
		compName = compName.substring(0, 1).toLowerCase() + compName.substring(1);
		compName = compName + "Info";
		url = base + compName;
	}
	newwin = window.open(url, helpWinName);
	if(window.focus)
	{
		newwin.focus();
	}
	return false;
}

$(document).ready(function()
{
	$(".helpLink").click(showHelp);
});

