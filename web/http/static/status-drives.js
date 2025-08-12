
function drivesBuild(data)
{
	var table = document.createElement("table");
	table.classList.add("status-drives");

	var tr = document.createElement("tr");
	var tr_names = document.createElement("tr");

	for (const [key, value] of Object.entries(data))
	{
		var td = document.createElement("td");
		console.log(key)

		td.innerText = value["name"];
		td.id = "driveStatus_"+key;
		td.onclick = function() { drivesUpdateAction(key); };
		tr.appendChild(td);

		td = document.createElement("td");
		td.id = "driveStatus_media_"+key;
		td.innerText = value["media"];
		tr_names.appendChild(td);
	}
	built=true;
	table.appendChild(tr);
	table.appendChild(tr_names);
	return table
}
built=false

function drivesUpdateAction(drive)
{
	var data = {"drive_status":{
		[drive] : {
			"action": Math.floor(Date.now() / 1000)
		}
	}};
	fetch("/update", {
		method: "POST",
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify(data)
	}).then(res => {
		console.log("Request complete! response:", res);
	});
}

function drivesLoadStatus(event)
{
	fetch('/status/drive_status.json').then((response) => response.json())
	.then((data) =>
		{
			elm = document.getElementById("status-drives")
			if (!built)
				elm.appendChild(drivesBuild(data));

			for (const [key, value] of Object.entries(data))
			{
				drive=document.getElementById("driveStatus_"+key);
				drive.className = '';
				switch(value["status"])
				{
					case 0:
						drive.classList.add("idle");
						break;
					case 1:
						drive.classList.add("good");
						break;
					case 2:
					case 4:
						drive.classList.add("working");
						break;
					case 3:
						drive.classList.add("attention");
						break;
				}

				if ("title" in value)
				{
					drive.title = value["title"];
				}
				drive=document.getElementById("driveStatus_media_"+key);
				drive.innerText = value["media"];
			}
		}
	);


	setTimeout(drivesLoadStatus, 3000);
}
window.addEventListener("load", drivesLoadStatus);

