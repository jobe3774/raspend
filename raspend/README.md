# raspend - a small and easy to use HTTP backend framework for the Raspberry Pi

First of all, it should be mentioned that **raspend** was originally intended to be a backend framework for the Raspberry Pi, but since it was written entirely in Python, it can be used on any platform with a Python interpreter. 

As you can imagine **raspend** is the abbreviation for **rasp**berry back**end**.

## Motivation

Since I am doing a lot of home automation stuff on the Raspberry Pi and since the third Python script for that had the same structure, I decided to create an easy to use framework to simplify my life for when I start my next project on my RPi. Further I just wanted to strengthen my Python skills. This is why I didn't use any of the available frameworks such as flask or wsgiref.

## Now, what does this framework provide?

As 'backend' already suggests it, this framework provides you with an easy way of creating a small HTTP web service on your RPi. The **RaspendHTTPServerThread** class is based on Python's **HTTPServer** class which is executed in its own thread. Besides that, it provides you also with an easy way of acquiring data (e.g. temperatures measurements) in a multithreaded way.

The one idea is that the data acquisition threads you write all use a shared dictionary to store their data. The HTTP server thread knows this dictionary too and exposes it as a JSON string via HTTP GET requests.

By the way, you only need to write a handler deriving the **DataAcquisitionHandler** class and provide it to the respective instance of **DataAcquisitionThread**.

``` python
from raspend.http import RaspendHTTPServerThread
import raspend.utils.dataacquisition as DataAcquisition

class myDataAcquisitionHandler(DataAcquisition.DataAcquisitionHandler):
    def __init__(self, name, dataDict = None):
        self.name = name
        return super().__init__(dataDict)

    def acquireData(self):
        if not self.name in self.dataDict:
            self.dataDict[self.name] = {"loop" : 1}
        else:
            self.dataDict[self.name]["loop"] += 1

...

dataGetter1 = myDataAcquisitionHandler("dataGetter1", dataDict)
dataThread1 = DataAcquisition.DataAcquisitionThread(3, shutdownFlag, dataLock, dataGetter1)

httpd = RaspendHTTPServerThread(shutdownFlag, dataLock, dataDict, None, args.port)

dataThread1.start()
httpd.start()
```

The other idea was it to expose different functionalities, such as switching a light bulb via GPIO, as a command you can send to your RPi via HTTP POST request. All you have to do is to encapsulate the functionality you want to make available to the outside world into a method of a Python class. Then instantiate your class and create a new **Command** object to which you pass your method. In another step, add this **Command** object to the so-called **CommandMap**. You then pass this **CommandMap** in the constructor to the instance of your **RaspendHTTPServerThread**. Now you can execute your method using a simple HTTP POST request. 

``` python
from raspend.http import RaspendHTTPServerThread
import raspend.utils.commandmapping as CommandMapping

class DoorBell():
    def __init__(self, *args, **kwargs):
        self.doorBellState = "on"

    def switchDoorBell(self, onoff):
        if type(onoff) == str:
            self.doorBellState = "on" if onoff == "on" else "off"
        elif type(onoff) == int:
            self.doorBellState = "on" if onoff >= 1 else "off"
        else:
            raise TypeError("State must be 'int' or 'string'.")
        return self.doorBellState

    def getCurrentState(self):
        return self.doorBellState

...

theDoorBell = DoorBell()

cmdMap = CommandMapping.CommandMap()

cmdMap.add(CommandMapping.Command(theDoorBell.switchDoorBell))
cmdMap.add(CommandMapping.Command(theDoorBell.getCurrentState))

httpd = RaspendHTTPServerThread(shutdownFlag, dataLock, dataDict, cmdMap, args.port)

httpd.start()
``` 

Please have a look at the examples included in this project to get a better understanding.

## How to use the HTTP interface?

### The data part

As mentioned above, the data acquisition side of your web service writes its data to a shared dictionary you provide it with. You can query this data by sending a HTTP GET request to **http://<your-raspberrypi's-ip:port>/data**. Your **RaspendHTTPServerThread** then sends the whole shared dictionary as a JSON string. 

Lets say you are measuring the temperatures of different rooms of your house's floors, then the shared dictionary could have the following structure:

```
{
    "basement" : {
        "party_room": 17.8,
        "heating_room": 18,
        "fitness_room": 19.5
    },
    "ground_floor" : {
        "kitchen": 23.5,
        "living_room", 23.6
    }
}
```

If you only want to know the temperatures for the ground floor you can request **/data/ground_floor**. Then the response would be:

```
"ground_floor" : {
        "kitchen": 23.5,
        "living_room", 23.6
    }
```

Or if you only want to know the temperature of the fitness room in your basement you could use **/data/basement/fitness_room** and the response would be:

```
19.5
```

### The command part

Now lets have a look at the command interface of **raspend**. If you want to know which commands are available you can request **/cmds**. Then the response for the above mentioned example would be:

```
{
  "Commands": [{
      "Command": {
          "Name": "theDoorBell.switchDoorBell",
          "Args": {
              "onoff": ""
          }
      }
  }, {
      "Command": {
          "Name": "theDoorBell.getCurrentState",
          "Args": {}
      }
  }]
}
```

As you can see in the response above, your variable names should be in a more descriptive manner, since the instance of your Python class is used instead of the class name. 

You invoke a command by sending it's call information as described in the list above via HTTP POST request. Here an JavaScript example:

``` javascript

let payload = {
    Command : {
        Name : "theDoorBell.switchDoorBell",
        Args : {
            onoff : "off"
        }
    }
};

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
    console.log(responsePayload);
}
    
``` 

The **RaspendHTTPServerThread** receives

``` 
{
  "Command": {
    "Name": "theDoorBell.switchDoorBell",
    "Args": {
       "onoff": "off"
    }
  }
}
``` 

and invokes the method. The response of this HTTP-POST request will be your JSON enhanced with the result of the method invocation:

``` 
{
  "Command": {
    "Name": "theDoorBell.switchDoorBell",
    "Args": {
       "onoff": "off"
    },
    "Result": "off"
  }
}
``` 

Any other information contained in your JSON data will stay untouched. So you can attach any other information with that command such as an element-id of your frontend invoking it.

## How to install?

```
   pip install raspend
```