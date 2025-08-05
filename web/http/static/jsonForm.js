/* jsonForm
 *
 * Takes a json url or data object and creates a form out of named keys.
 */
class jsonForm
{

constructor(dataSource=null, element=null,title="Form",options=null)
{
	options ||= {"top_blank":false,"form_names":false};
	this.element = element;
	this.id = this.element.id;
	this.title = title;
	this.options = options;
	this.textarea = null;
	if (typeof dataSource == "object")
	{
		// Is data
		this.defaultData = dataSource;
		this.objectToForm(this.defaultData,title);

	}else if(typeof dataSource == "string")
	{
		// Is URL
		fetch(dataSource).then((response) => response.json())
		.then((data) =>
			{
			this.defaultData = data;
			this.objectToForm(this.defaultData,title);
			}
		);
	}
}


objectToForm(data,title=null)
{
	// WARNING RECURSIVE
	if (data == null) return null;

	// Wipe out element
	this.element.replaceChildren();

	var options = document.createElement("div");

	if (title != null)
	{
		var formtitle = document.createElement("h2");
		formtitle.innerText=title;
		this.element.append(formtitle);
	}
	this.element.append(...this.objectHTML(data,null).children);
	var controls = document.createElement("div");
	controls.classList.add("objectform_controls");
	//             <input type="button" id="config_download" value="Save Config" />
	var btn_save = document.createElement("input");
	btn_save.type = "button";
	btn_save.id = this.id+"_download";
	btn_save.value = "Save Form Data";
	btn_save.addEventListener('click', this.download.bind(this));

	controls.append(btn_save);

	var btn_file_upload = document.createElement("input");
	btn_file_upload.type = "file";
	btn_file_upload.id = this.id+"_file_upload";
	btn_file_upload.addEventListener('change', this.upload.bind(this));
	controls.append(btn_file_upload);

	this.textarea = document.createElement("textarea");
	this.textarea.name = this.id+"_json_data";
	this.textarea.id = this.id+"_json_data";
	this.textarea.style = "display:none;";
	controls.append(this.textarea);

	this.element.append(controls);
}

objectHTML(data,prefix="")
{
	// WARNING RECURSIVE
	if (data == null) return null;

	// Wipe out element

	var options = document.createElement("div");
	var prefix_str = "";

	for (const [key, value] of Object.entries(data))
	{
		if(value == null || typeof value != "object")
		{
			// Option to skip top level unused settings
			if (prefix == null && this.options.top_blank) continue;

			var pair = document.createElement("div");
			pair.classList.add("object_form_data");
			// Add Label with key
			var label = document.createElement("label");
			label.innerText=key.substring(0,1).toUpperCase()+key.substring(1).toLowerCase();
			label.htmlFor=prefix+"|"+key;
			// Add input with name for value
			var input = document.createElement("input");
			if (this.options.form_names)
				input.name=prefix+"|"+key;
			input.id=prefix+"|"+key;
			input.value=value;
			pair.appendChild(label);
			pair.appendChild(input);
			options.appendChild(pair);
		}else{
			// New fieldset
			prefix_str = prefix == null ? "" : prefix+"|";

			var fieldset = document.createElement("fieldset");
			// Add legend with key
			var legend = document.createElement("legend");
			legend.id=prefix_str+key;
			legend.innerText=key.substring(0,1).toUpperCase()+key.substring(1).toLowerCase();
			fieldset.appendChild(legend);
			// Go deeper
			var child=this.objectHTML(value,prefix_str+key);
			if (child != null) fieldset.appendChild(child);

			options.appendChild(fieldset);
		}

	}
	return options;
}

// TODO - FormtoObject to submit data. Also allows uploading json file instead. And user could save json file to reuse
formToObject()
{
	var data={};
	// Get all inputs in form object from ID
	var sel="#"+this.id+" .object_form_data input";
	var base=document.querySelectorAll(sel);
	// Handle each input
	for (const child of base)
	{
		// If there is not data, skip
		//if ( child.value == "") continue;

		// Copy data refrence
		var walk=data;
		// Get array of keys from ID
		var keys = child.id.split("|")
		// Stor last key wh
		var lastkey=keys.pop();
		for (const key of keys)
		{
			// insantiate new object if undefined(false)
			walk[key] ||= {};
			// Move walk refrence to lower key
			walk = walk[key];
		}
		// Set final key to value
		walk[lastkey] = child.value;
	}
	return data;
}

objectUpdate(base,update)
{
	// WARNING RECURSIVE

	for (const [key, value] of Object.entries(update))
	{
		if(typeof value != "object")
		{
			try{
				base[key] = value;
			} catch (error) {
				console.error(error);
			}
		}else{
			base[key] = this.objectUpdate(base[key],value);
		}
	}
	return base;
}

prepare()
{
	this.textarea.value = JSON.stringify(this.formToObject());
}

// Download
download(filename, text) {
	this.prepare();

	var element = document.createElement('a');
	element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(this.textarea.value));
	element.setAttribute('download', "config_data.json");

	element.style.display = 'none';
	document.body.appendChild(element);

	element.click();

	document.body.removeChild(element);
}
//document.getElementById("config_download").addEventListener('click', download);

// Download
async upload(filename, text) {

    const [file] = document.getElementById(this.id+"_file_upload").files;

    if (file) {
        var loadData =  JSON.parse( await file.text() );
		loadData = this.objectUpdate(this.defaultData,loadData)

		//data = { ...default_config, ...loadData };
		var form=document.getElementById('config_options');
		this.objectToForm(loadData,this.title);
    }
}
//document.getElementById("completeLoad").addEventListener('change', upload);


}
