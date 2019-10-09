# raspend - a small and easy to use HTTP backend framework for the Raspberry Pi

First of all, it should be mentioned that **raspend** was originally intended to be a backend framework for the Raspberry Pi, but since it was written entirely in Python, it can be used on any platform with a Python interpreter. 

As you can imagine **raspend** is the abbreviation for **rasp**berry back**end**.

## Motivation

Since I am doing a lot of home automation stuff on the Raspberry Pi and since the third Python script for that had the same structure, I decided to create an easy to use framework to simplify my life for when I start my next project on my RPi. Further I just wanted to strengthen my Python skills. This is why I didn't use any of the available frameworks such as flask or wsgiref.

## Now, what does this framework provide?

As 'backend' already suggests, this framework provides you with an easy way of creating a small HTTP web service on your RPi. The **RaspendApplication** class runs the **RaspendHTTPServerThread**, which is based on Python's **HTTPServer** class, to handle incoming HTTP requests. Besides that, this framework provides you with an easy way of acquiring data (e.g. temperatures measurements) in a multithreaded way.

The one idea is, that the data acquisition threads you create all use one shared dictionary to store their data. The HTTP server thread knows this dictionary too and exposes it as a JSON string via HTTP GET requests.

You only need to write a handler deriving the **DataAcquisitionHandler** class and call the **createDataAcquisitionThread** method of **RaspendApplication** to create a new instance of a **DataAcquisitionThread**. The **RaspendApplication** class manages the list of your threads.


``` python
from raspend.application import RaspendApplication
from raspend.utils import dataacquisition as DataAcquisition

class ReadOneWireTemperature(DataAcquisition.DataAcquisitionHandler):
    def __init__(self, groupId, sensorId, oneWireSensorPath = ""):
        # A groupId for grouping the temperature sensors
        self.groupId = groupId
        # The name or Id of your sensor under which you would read it's JSON value
        self.sensorId = sensorId
        # The path of your sensor within your system
        self.oneWireSensorPath = oneWireSensorPath

    def acquireData(self):
        # If you use 1-Wire sensors like a DS18B20 you normally would read its w1_slave file like:
        # /sys/bus/w1/devices/<the-sensor's system id>/w1_slave
        temp = random.randint(18, 24)

        if not self.groupId in self.dataDict:
            self.dataDict[self.groupId] = {self.sensorId : temp}
        else:
            self.dataDict[self.groupId][self.sensorId] = temp
        return


myApp = RaspendApplication(8080)

myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "party_room", "/sys/bus/w1/devices/23-000000000001/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "heating_room", "/sys/bus/w1/devices/23-000000000002/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "fitness_room", "/sys/bus/w1/devices/23-000000000003/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("ground_floor", "kitchen", "/sys/bus/w1/devices/23-000000000004/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("ground_floor", "living_room", "/sys/bus/w1/devices/23-000000000005/w1_slave"), 30)

myApp.run()

```

The other idea is to expose different functionalities, such as switching on/off your door bell via GPIO, as a command you can send to your RPi via HTTP POST request. All you have to do is to encapsulate the functionality you want to make available to the outside world into a method of a Python class. Then instantiate your class and call the **addCommand** method of **RaspendApplication** providing the method you want to expose. Now you can execute your method using a simple HTTP POST request. 

``` python
from raspend.application import RaspendApplication

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

myApp = RaspendApplication(8080)

theDoorBell = DoorBell()

myApp.addCommand(theDoorBell.switchDoorBell)
myApp.addCommand(theDoorBell.getCurrentState)

myApp.run()

``` 

When all initialization stuff is done (adding commands, creating data acquisition threads), then you start your application by calling the **run** method of **RaspendApplication**. The **RaspendApplication** class installs signal handlers for SIGTERM and SIGINT, so you can quit your application by pressing CTRL+C or sending one of the signals via the **kill** command of your shell.

Please have a look at the examples included in this project to get a better understanding. *example1.py* and *example2.py* show how to do most of the work yourself, while *example3.py* shows you the most convenient way of using this framework.

## How to use the HTTP interface?

### The data part

As mentioned above, the data acquisition side of your web service writes its data to a shared dictionary. You can query this data by sending a HTTP GET request to **http://<your-raspberrypi's-ip:port>/data**. The **RaspendHTTPServerThread** then sends the whole shared dictionary as a JSON string. 

Let's say you are measuring the temperatures of different rooms of your house, then the shared dictionary could have the following structure:

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

If you only want to know the temperatures of the ground floor you can request **/data/ground_floor**. Then the response would be:

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

Now let's have a look at the command interface of **raspend**. If you want to know which commands are available you can request **/cmds**. Then the response for the above mentioned example would be:

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
    Command: {
        Name: "theDoorBell.switchDoorBell",
        Args: {
            onoff: "off"
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

if (response.status == 200) {
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

and invokes the method. The response of this HTTP POST request will be your JSON enhanced with the result of the method invocation:

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
Since remain untouched, you can attach any other information with that command such as an element-id of your frontend invoking it.

Starting with version 1.1.0, you can also use HTTP GET requests to invoke commands. The request has to following structure:

```
 /cmd?name=command&arg1=val1&arg2=val2...&argN=valN
```

So for the above mentioned example **theDoorBell.switchDoorBell**, the correct request would be:

```
 /cmd?name=theDoorBell.switchDoorBell&onoff=off
```

The **RaspendHTTPServerThread** invokes the command and responds with the result of the invocation as a JSON string.

## How to install?

Make sure you have installed Python 3.5 or higher. I've tested the package on my Raspberry Pi 3 Model B+ running **Raspbian GNU/Linux 9 (stretch)** with Python 3.5.3 installed. 

Use
```
$ pip install raspend
```
or if Python 3 isn't the default use
```
$ pip3 install raspend
```
to install the package.

## License

MIT. See LICENSE file.