var settings={};
var default_config={}

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
	select.name=name;
	select.id=id;
	drivegroup = document.createElement("optgroup");
	drivegroup.label="Groups";
	groupcheck=[];
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
				if(!groupcheck.includes(value[i]["group"]))
				{
					groups=true;
					option = document.createElement("option");
					option.value=value[i]["group"];
					option.innerText=value[i]["group"];
					drivegroup.appendChild(option);

					groupcheck.push(value[i]["group"]);
				}
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
			settings = data; document.getElementById('media_drive').replaceWith(buildOptionGroupList(settings["drives"],"media_drive","media_drive"));
		}
	);
}
window.addEventListener("load", markerCustomAdd);


jform = new jsonForm(
	'/config_data.json',
	document.getElementById('config_options'),
	'Config Options',
	{"top_blank":true,"form_names":false},
	{"FLUX|diskdefs-direct":"textarea"}
)

function sendMediaForm()
{
	ts = Date.now().toString().replace(":","-")
	jform.prepare();
	const data = new URLSearchParams();
	for (const pair of new FormData(document.getElementById('media_form'))) {
		if (document.getElementById('name_timestamp').checked && pair[0] == 'media_name') pair[1] = ts+"_"+pair[1]
		data.append(pair[0], pair[1]);
	}

	fetch("/rip", {
		method: 'post',
		body: data,
	}).then(() => {
		document.getElementById('media_name').value = "";
		document.getElementById('media_description').value = "";
	});
}
document.getElementById('send_media_form').onclick = function() { sendMediaForm(); };
