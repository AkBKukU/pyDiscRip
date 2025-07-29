var settings={};

function buildOptionGroupList(data,id,name)
{
	/*
	 < div *class="input_pair">
	 <label for="media_type">Type:</label>
	 <select name="media_type" id="media_type">
		<optgroup label="Optical">
			<option value="AUTO">Auto (Optical Only)</option>
			<option value="CD">CD</option>
			<option value="DVD">DVD</option>
		</optgroup>
		<optgroup label="Greaseweazle">
			<option value="FLOPPY">Floppy</option>
		</optgroup>
	 </select>
	 <div>
	 */
	select = document.createElement("select");
	select.attributes.name=name;
	select.id=id;
	drivegroup = document.createElement("optgroup");
	drivegroup.label="Groups";
	groups=false;
	for (const [key, value] of Object.entries(data))
	{
		console.log(key);
		optgroup = document.createElement("optgroup");
		optgroup.label=key;
		for (var i = 0; i < value.length; ++i) {
			option = document.createElement("option");
			option.value=value[i]["drive"];
			option.innerText=value[i]["name"];
			optgroup.appendChild(option);
			if ("group" in value[i])
			{
				groups=true;
				option = document.createElement("option");
				option.value=value[i]["group"];
				option.innerText=value[i]["group"];
				drivegroup.appendChild(option);

			}
		}
		if(groups) select.appendChild(drivegroup);
		select.appendChild(optgroup);
	}
	return select
}

function markerCustomAdd(event)
{
	fetch('/settings.json').then((response) => response.json())
	.then((data) =>
		{
			settings = data; document.getElementById('media_drive').replaceWith(buildOptionGroupList(settings["drives"],"media_type","media_type"));
		}
	);
}
window.addEventListener("load", markerCustomAdd);
