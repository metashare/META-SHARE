
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

