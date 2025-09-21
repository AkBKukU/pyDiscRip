function mediaSampleView(media_sample)
{
	var table = document.createElement("table");
	table.classList.add("status-view");

	var tr = document.createElement("tr");

	// ROW1 - Name Header
	var h3 = document.createElement("h3");
	var th = document.createElement("th");
	h3.innerText=media_sample["name"];
	th.colSpan = 100;
	th.appendChild(h3);
	tr.appendChild(th);

	table.appendChild(tr);


	// ROW2 - Preview image
	tr = document.createElement("tr");
	var td = document.createElement("td");
	var row =3;
	if ("time_added" in media_sample) row+=1;
	if ("time_start" in media_sample) row+=1;
	if ("time_end" in media_sample) row+=1;
	td.rowSpan = row;
	var img = document.createElement("img");
	if (media_sample["media_type"] == "FLOPPY" && !( media_sample["data"] === undefined))
	{
		for (const data of media_sample["data"])
		{
			if (data["type_id"]=="IMAGE")
			{
				img.src = "/output/"+data["data_dir"]+"/"+data["data_files"]["PNG"]
			}
		}
	}
	if (media_sample["media_type"] == "CD" && !( media_sample["data"] === undefined))
	{
		for (const data of media_sample["data"])
		{
			if (data["type_id"]=="IMAGE")
			{
				img.src = "/output/"+data["data_dir"]+"/"+data["data_files"]["JPG"]
			}
		}
	}
	td.appendChild(img);
	tr.appendChild(td);

	// ROW2 - Description
	td = document.createElement("td");
	td.innerText="Description";
	tr.appendChild(td);
	td = document.createElement("td");
	td.innerText=media_sample["description"];
	tr.appendChild(td);

	table.appendChild(tr);

	// ROW3 - Media Type
	tr = document.createElement("tr");
	td = document.createElement("td");
	td.innerText="Media Type";
	tr.appendChild(td);
	td = document.createElement("td");
	td.innerText=media_sample["media_type"];
	tr.appendChild(td);

	table.appendChild(tr);

	// ROW4 - Drive
	tr = document.createElement("tr");
	td = document.createElement("td");
	td.innerText="Drive";
	tr.appendChild(td);
	td = document.createElement("td");
	td.innerText=media_sample["drive"];
	tr.appendChild(td);

	table.appendChild(tr);

	// ROW5 - Drive
	if ("time_added" in media_sample)
	{
		tr = document.createElement("tr");
		td = document.createElement("td");
		td.innerText="Added";
		tr.appendChild(td);
		td = document.createElement("td");
		td.innerText=media_sample["time_added"];
		tr.appendChild(td);

		table.appendChild(tr);
	}

	// ROW6 - Drive
	if ("time_start" in media_sample)
	{
		tr = document.createElement("tr");
		td = document.createElement("td");
		td.innerText="Start";
		tr.appendChild(td);
		td = document.createElement("td");
		td.innerText=media_sample["time_start"];
		tr.appendChild(td);

		table.appendChild(tr);
	}

	// ROW7- Drive
	if ("time_end" in media_sample)
	{
		tr = document.createElement("tr");
		td = document.createElement("td");
		td.innerText="End";
		tr.appendChild(td);
		td = document.createElement("td");
		td.innerText=media_sample["time_end"];
		tr.appendChild(td);

		table.appendChild(tr);
	}

	if ( media_sample["data"] === undefined) return table;
	// ROW8 - Data Header
	tr = document.createElement("tr");
	var h4 = document.createElement("h4");
	th = document.createElement("th");
	h4.innerText="Data Outputs";
	th.colSpan = 100;
	th.appendChild(h4);
	tr.appendChild(th);

	table.appendChild(tr);

	// ROW8+N - Data Outputs
	for (const data of media_sample["data"])
	{
		tr = document.createElement("tr");
		td = document.createElement("td");
		td.innerText=data["type_id"];
		data_files_array = Object.entries(data["data_files"])
		td.rowSpan=data_files_array.length;
		tr.appendChild(td);


		row_left=data_files_array.length;
		for (const [key, value] of data_files_array)
		{
				td = document.createElement("td");
				td.innerText=key;
				tr.appendChild(td);

			td = document.createElement("td");
			if ( Array.isArray(value) )
			{
				var ul = document.createElement("ul");
				var limit=20;
				for (const file of value)
				{
					var li = document.createElement("li");
					li.innerText=file;
					ul.appendChild(li);
						limit-=1;
						if(!limit)
						{
							var li = document.createElement("li");
							li.innerText="...";
							ul.appendChild(li);
							break;
						}
				}
				td.appendChild(ul);

			} else {
				if(typeof value === "object")
				{
					var ul = document.createElement("ul");
					var limit=20;
					for (const [type, path] of Object.entries(value))
					{
						var li = document.createElement("li");
						li.innerText=type+":"+path;
						ul.appendChild(li);
						limit-=1;
						if(!limit)
						{
							var li = document.createElement("li");
							li.innerText="...";
							ul.appendChild(li);
							break;
						}
					}
					td.appendChild(ul);

				}else if(typeof value === "string")
				{
					td.innerText=value;
				}
			}
			tr.appendChild(td);

			if(row_left > 1)
			{
				row_left-=1;
				table.appendChild(tr);
				tr = document.createElement("tr");
			}
		}
		table.appendChild(tr);
	}


	return table;
}


function loadStatus(event)
{
	fetch('/status/status.json').then((response) => response.json())
	.then((data) =>
		{
			document.getElementById("status").replaceChildren();

			data.sort(function(a, b) {
				var adate = a.time_added.split('T')[0]+"T"+a.time_added.split('T')[1].replaceAll("-",":");
				var bdate = b.time_added.split('T')[0]+"T"+b.time_added.split('T')[1].replaceAll("-",":");
				var keyA = new Date(adate),
					 keyB = new Date(bdate);
					 // Compare the 2 dates
					 if (keyA < keyB) return 1;
					 if (keyA > keyB) return -1;
					 return 0;
			});

			for (const media_sample of data)
			{
				table=mediaSampleView(media_sample);
			document.getElementById("status").appendChild(table);
			}
		}
	);


	setTimeout(loadStatus, 3000);
}
window.addEventListener("load", loadStatus);

