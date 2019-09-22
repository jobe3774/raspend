var g_baseUrl = "http://raspberrypi:8090";
//var g_baseUrl = "http://localhost:8090";

function onInit()
{
    httpGetAsync(g_baseUrl+"/cmds", populateCommandList);
}

function populateCommandList(resp)
{
    let cmdList = resp.Commands;

    window.cmdList = cmdList;

    let basicRowHTMLTemplate = `<td class="align-middle">%CMDNAME%</td>
    <td>
        <button type="button" class="btn btn-primary" onclick="onInvoke('%CMDNAME%')">Invoke</button>
    </td>`;

    let inputArgHTMLTemplate = `<td>
        <input type="text" class="form-control" id="%CMDNAME%.%ARGNAME%" placeholder="%ARGNAME%">
    </td>`;

    let commandTable = document.getElementById("commandList");

    for (i=0; i < cmdList.length; i++)
    {
        let cmd = cmdList[i].Command;
        let row = commandTable.insertRow(-1);

        let basicRowHTML = basicRowHTMLTemplate.replace(/%CMDNAME%/g, cmd.Name);
        let rowHTML = basicRowHTML;

        if (cmd.hasOwnProperty("Args"))
        {
            for (let arg in cmd.Args)
            {
                let inputArgHTML = inputArgHTMLTemplate.replace(/%CMDNAME%/g, cmd.Name);
                inputArgHTML = inputArgHTML.replace(/%ARGNAME%/g, arg);
                rowHTML += inputArgHTML;
            }
        }

        row.innerHTML = rowHTML;
    }
}

function onInvoke(commandName)
{
    if (!window.hasOwnProperty("cmdList"))
    {
        console.log("Error: Command list not avaiable!");
        return;
    }

    let payload = {};

    for (i=0; i < window.cmdList.length; ++i)
    {
        let cmd = window.cmdList[i].Command;

        if (cmd.Name === commandName)
        {
            payload["Command"] = {"Name" : cmd.Name};

            if (cmd.hasOwnProperty("Args"))
            {
                payload["Command"]["Args"] = {};
                for (let arg in cmd.Args)
                {
                    let elemId = cmd.Name + "." + arg;
                    let elem = document.getElementById(elemId);

                    let elemVal = elem.value;

                    payload["Command"]["Args"][arg] = elemVal;
                }
            }
            
            httpPostAsync(g_baseUrl, payload, onCmdResult);
        }
    }

    console.log("invoking '" + commandName + "' ...");
}

function onCmdResult(response)
{
    debugConsole = document.getElementById("debugConsole");
    debugConsole.innerText += response + "\n";
    console.log("Result of method invocation: " + response);
}

async function httpGetAsync(theUrl, callback)
{
  let response = await fetch(theUrl);

  if (response.status == 200)
  {
    let json = await response.json();
    callback(json);
  }
}

async function httpPostAsync(theUrl, payload, callback) 
{
    let response = await fetch(theUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=utf-8'
        },
        body: JSON.stringify(payload)
    });

    if (response.status == 200)
    {
        let responsePayload = await response.json();
        callback(JSON.stringify(responsePayload));
    }
}