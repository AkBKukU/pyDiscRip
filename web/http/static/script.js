var settings={};

function markerCustomAdd(event)
{
	fetch('/settings.json').then((response) => response.json())
	.then(
		(data) => {
			settings = data;
			alert(settings["web"]["ip"]);
		}
	);
}
window.addEventListener("load", markerCustomAdd);
