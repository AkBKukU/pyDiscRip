
function queueBuild(data)
{
    var table = document.createElement("table");
    table.classList.add("status-drives");

    var tr = document.createElement("tr");

    for (const [key, value] of Object.entries(data))
    {
        var td = document.createElement("td");
        console.log(key)

        td.innerText = value["name"];
        td.id = "driveStatus_"+key;
        tr.appendChild(td);
        td.onclick = function() { drivesUpdateAction(key); };
    }
    built=true;
    table.appendChild(tr);
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

function toggle_pause() {
fetch('/pause')
}


function queue_status() {
    queue_stat={}
fetch('/status/queue_status.json').then((response) => response.json())
    .then((data) =>
    {
        return  data
    });
}

function queueLoadStatus(event)
{
    fetch('/status/queue.json').then((response) => response.json())
    .then((data) =>
    {
        document.getElementById("queue").replaceChildren();

        var table = document.createElement("table");
        var tr = document.createElement("tr");
        var th = document.createElement("th");
        th.innerText = "Queue";
        th.colSpan = 2;
        tr.appendChild(th);
        table.appendChild(tr);

        tr = document.createElement("tr");
        th = document.createElement("td");
        var label = document.createElement("label");
        var input = document.createElement("input");
        th.colSpan = 2;
        fetch('/status/queue_status.json').then((response) => response.json())
        .then((data) =>
        {
            input.checked = data["pause"];
        });
        label.innerText = "Queue Pause";
        label.for = "queue_pause";
        input.type = "checkbox";
        input.id = "queue_pause";
        input.name = "queue_pause";
        input.addEventListener('click', toggle_pause);

        th.appendChild(label);
        th.appendChild(input);
        tr.appendChild(th);
        table.appendChild(tr);

        tr = document.createElement("tr");
        th = document.createElement("th");
        th.innerText = "Sample";
        tr.appendChild(th);
        th = document.createElement("th");
        th.innerText = "Source";
        tr.appendChild(th);
        table.appendChild(tr);

        for (i in data)
        {
            if (data[i]["done"]) continue;

            tr = document.createElement("tr");
            var td = document.createElement("td");
            td.innerText = data[i]["name"];
            tr.appendChild(td);

            td = document.createElement("td");
            if ("group" in data[i])
            {
                td.innerText = data[i]["group"];
            }else{
                td.innerText = data[i]["drive"];
            }
            tr.appendChild(td);
            table.appendChild(tr);
        }


        document.getElementById("queue").appendChild(table);
    }
    );


    setTimeout(queueLoadStatus, 3000);
}
window.addEventListener("load", queueLoadStatus);

