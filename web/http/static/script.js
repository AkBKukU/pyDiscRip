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

function objectToForm(data,id="object_form",prefix="")
{
	if (data == null) return null;

	var options = document.createElement("div");
	if (prefix == "" || prefix == null) options.id=id;
	// WARNING RECURSIVE
	for (const [key, value] of Object.entries(data))
	{
		if(value == null || typeof value != "object")
		{
			// Option to skip top level unused settings
			if (prefix == null) continue;

			var pair = document.createElement("div");
			pair.classList.add("input_pair");
			// Add Label with key
			var label = document.createElement("label");
			label.innerText=key.substring(0,1).toUpperCase()+key.substring(1).toLowerCase();
			label.htmlFor=prefix+"|"+key;
			// Add input with name for value
			var input = document.createElement("input");
			input.name=prefix+"|"+key;
			input.id=prefix+"|"+key;
			input.value=value;
			pair.appendChild(label);
			pair.appendChild(input);
			options.appendChild(pair);
		}else{
			// New fieldset

			var fieldset = document.createElement("fieldset");
			// Add legend with key
			var legend = document.createElement("legend");
			legend.id=prefix+"|"+key;
			legend.innerText=key.substring(0,1).toUpperCase()+key.substring(1).toLowerCase();
			fieldset.appendChild(legend);
			// Go deeper
			child=objectToForm(value,key);
			if (child != null) fieldset.appendChild(child);

			options.appendChild(fieldset);
		}

	}
	return options;
}
// TODO - FormtoObject function to submit data. Also allows uploading json file instead. And user could save json file to reuse
function formToObject(base)
{
	data={};
	for (const child of base.children) {
		console.log(child.tagName);
		console.log(child.children.length);
	}


	//download("form.json",JSON.stringify(saveData));
}

// Download
function download(filename, text) {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}

function loadConfigOptions(event)
{
	fetch('/config_data.json').then((response) => response.json())
	.then((data) =>
		{
			form=document.getElementById('config_options')
			form.replaceWith(objectToForm(data,'config_options',null));
			form=document.getElementById('config_options')
			formToObject(form);
		}
	);
}
window.addEventListener("load", loadConfigOptions);
