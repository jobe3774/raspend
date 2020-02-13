# raspend - a lightweight web service framework

## Motivation

Since I am doing a lot of home automation stuff on my Raspberry Pi and since the third Python script for that had the same structure, I decided, strictly following the [DRY principle](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself), to create an easy to use framework to simplify my life for when I start my next project on my RPi.

## Introduction

It should be mentioned that **raspend**, which is the abbreviation for **rasp**berry back**end**, was originally intended to be a web service framework for the Raspberry Pi. But since it's written entirely in Python and has no RPi specific code or dependencies, it can be used on any platform having a Python interpreter installed.

**raspend** combines two core features. The first is the data processing part, where one or more threads share the same *dictionary* they read from or write to. The data contained in this shared dictionary is exposed to the outside world through an HTTP interface as a JSON string. Therefore the HTTP interface provides the */data* endpoint. The second feature is providing an easy to use interface, which lets you invoke your self-defined commands via the already mentioned HTTP interface. (see [How to use the HTTP interface](#how-to-use-the-http-interface) for more details)

**raspend** comes with a ready-to-use application class called **RaspendApplication**. It manages your threads, your commands and the HTTP interface. Pass the port number, the HTTP interface should listen on, to the constructor of **RaspendApplication**. If you don't want to expose any data or invoke any commands on your system via HTTP interface, you can put **RaspendApplication** into "offline" mode by passing *None* instead of a port number. 

When all initialization stuff is done (adding commands, creating threads), then you start your application by calling the **run** method of **RaspendApplication**. The **RaspendApplication** class installs signal handlers for SIGTERM and SIGINT, so you can quit your application by pressing CTRL+C or sending one of the signals via the **kill** command of your shell. 

## Data processing with **raspend**

With **raspend**, creating threads is really simple and straight forward. All you need to do is, derive the **ThreadHandlerBase** class and implement the abstract methods *prepare* and *invoke*. The *prepare* method is called before the thread loop starts, while *invoke* will be called for every iteration of the thread loop. For tasks like cyclic reading temperature measurements or checking the CPU performance or something like that, you can use the **createWorkerThread** method of the **RaspendApplication** class. It takes an instance of your thread handler and a timeout value in seconds as parameters. The thread will sleep for *timeout* seconds past every iteration.

If you want a thread or task to do its work in a more scheduled way, such as run once a day, then you can use the **createScheduledWorkerThread** method of the **RaspendApplication** class. **createScheduledWorkerThread**, like **createWorkerThread**, takes an instance of your thread handler. But instead taking a timeout, you have to pass a start time, a start date, the type of repetition and a repetition factor. Start time and date can be *None*. If so, the current time and date will be used. If *repetitionType* is *None*, it defaults to **ScheduleRepetitionType.DAILY**. The repetition factor is applied to the repetition type and defaults to 1. For example, if you need to write your temperature measurements to a file every 15 minutes starting immediately, you would choose **ScheduleRepetitionType.MINUTELY** with a repetition factor set to 15 and start time and date set to *None*.

``` python
from raspend import RaspendApplication, ThreadHandlerBase, ScheduleRepetitionType

class ReadOneWireTemperature(ThreadHandlerBase):
    ...

class PublishOneWireTemperatures(ThreadHandlerBase):
    ...

class WriteOneWireTemperaturesToFile(ThreadHandlerBase):
    ...

# Create instance of the application class passing a port number for the HTTP interface.
myApp = RaspendApplication(args.port)

# Create worker threads for reading every temperature sensor once a minute.
myApp.createWorkerThread(ReadOneWireTemperature("basement", "party_room", "/sys/.../w1_slave"), 60)
myApp.createWorkerThread(ReadOneWireTemperature("basement", "heating_room", "/sys/.../w1_slave"), 60)
myApp.createWorkerThread(ReadOneWireTemperature("basement", "fitness_room", "/sys/.../w1_slave"), 60)
myApp.createWorkerThread(ReadOneWireTemperature("ground_floor", "kitchen", "/sys/.../w1_slave"), 60)
myApp.createWorkerThread(ReadOneWireTemperature("ground_floor", "living_room", "/sys/.../w1_slave"), 60)

# Publish temperatures to MySQL database every minute.
endPointURL = "http://localhost/raspend_demo/api/post_data.php"
myApp.createWorkerThread(PublishOneWireTemperatures(endPointURL, username, password), 60)

# Write temperatures to 1wire.csv every 15 minutes.
myApp.createScheduledWorkerThread(WriteOneWireTemperaturesToFile("./1wire.csv"), 
                                  None, 
                                  None, 
                                  ScheduleRepetitionType.MINUTELY, 
                                  15)

# Run main loop.
myApp.run()
```

## Making commands invocable with **raspend**

As mentioned earlier, **raspend's** second core feature is providing an easy way to let you invoke self-defined commands via its HTTP interface. Such a command must be implemented as a method of a Python class. This method then has to be passed to the **addCommand** method of **RaspendApplication**. You now can call this method with a simple HTTP GET or POST request. 

``` python
from raspend import RaspendApplication

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

# Create instance of the application class passing a port number for the HTTP interface.
myApp = RaspendApplication(args.port)

# Create instance of the class whos methods will be made invocable via HTTP interface.
theDoorBell = DoorBell()

# Add the methods as a command.
myApp.addCommand(theDoorBell.switchDoorBell)
myApp.addCommand(theDoorBell.getCurrentState)

# Run main loop.
myApp.run()
``` 

Please have a look at the examples included in this project. To see how I switch on/off my doorbell see [doorbell](https://github.com/jobe3774/doorbell). Another good example on how to use **raspend** is [mbpv](https://github.com/jobe3774/mbpv), which shows how I use **raspend's** worker threads to read out current values of my solar inverters. 

## How to use the HTTP interface?

### The data part

As already mentioned, all worker threads share the same dictionary they read from or write to. You can query this data by sending a HTTP GET request to **http://<ip-of-your-system:port>/data**. The HTTP interface then responds with the whole shared dictionary as a JSON string. It is recommended not to write too much data in this dictionary, as this could reduce performance.

Let's say you are measuring the temperatures of different rooms of your house, then the shared dictionary could have the following structure:

``` json
{
    "basement" : {
        "party_room": 17.8,
        "heating_room": 18,
        "fitness_room": 19.5
    },
    "ground_floor" : {
        "kitchen": 23.5,
        "living_room": 23.6
    }
}
```

If you only want to know the temperatures of the ground floor you can request **/data/ground_floor**. Then the response would be:

``` json
"ground_floor" : {
        "kitchen": 23.5,
        "living_room": 23.6
    }
```

Or if you only want to know the temperature of the fitness room in your basement you could use **/data/basement/fitness_room** and the response would be:

``` json
19.5
```

### The command part

Now let's have a look at the command interface of **raspend**. If you want to know which commands are available you can request **/cmds**. Then the response for the above mentioned *doorbell* example would be:

``` json
{
	"Commands": [{
			"Command": {
				"Name": "theDoorBell.switchDoorBell",
				"Args": {
					"onoff": "set to 'on' or 'off' without quotation marks"
				},
				"URL": "/cmd?name=theDoorBell.switchDoorBell&onoff="
			}
		}, {
			"Command": {
				"Name": "theDoorBell.getCurrentState",
				"Args": {},
				"URL": "/cmd?name=theDoorBell.getCurrentState"
			}
		}
	]
}
```

As you can see in the response above, your variable names should be in a more descriptive manner, since the instance of your Python class is used instead of the class name. Among other things, this allows us to have more than one instance of the respective class. 

You invoke a command by sending it's call information as described in the list above via HTTP POST request. 

Here a JavaScript example:

``` javascript

let payload = {
    Command: {
        Name: "theDoorBell.switchDoorBell",
        Args: {
            onoff: "off"
        }
    }
};

let response = await fetch("http://localhost:8080", {
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

The HTTP interface receives

``` json
{
  "Command": {
    "Name": "theDoorBell.switchDoorBell",
    "Args": {
       "onoff": "off"
    }
  }
}
``` 

and invokes the method. The response of this HTTP POST request will be **your** JSON enhanced with the result of the method invocation:

``` json
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

Starting with version 1.1.0, you can also use HTTP GET requests to invoke commands. The request has the following structure:

``` 
 /cmd?name=command&arg1=val1&arg2=val2...&argN=valN
```

So for the above mentioned example **theDoorBell.switchDoorBell**, the correct request would be:

``` 
 /cmd?name=theDoorBell.switchDoorBell&onoff=off
```

The HTTP interface invokes the command and responds with the result of the invocation as a JSON string.

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

## Remarks

There is a breaking change from version 1.4.0 to 2.0.0. The modules called **DataAcquisition** and **Publishing** fell victim to the DRY principle and have been replaced by the worker threads. This also means that the following methods have been removed from the **RaspendApplication** class: 
* **createDataAcquisitionThread**
* **createPublishDataThread**
* **createScheduledPublishDataThread**

Please use **createWorkerThread** or **createScheduledWorkerThread** instead. 

Migration should be easy. Just replace all derivations of **DataAcquisitionHandler** and **PublishDataHandler** by **ThreadHandlerBase**. Remove all ```from raspend.utils import dataacquisition as DataAcquisition``` and  ```from raspend.utils import publishing as Publishing``` and use ```from raspend import ThreadHandlerBase``` instead. In your implementations of **DataAcquisitionHandler** rename the **acquireData** method to **invoke**. In your implementations of **PublishDataHandler** rename the **publishData** method to **invoke** as well. 

## License

MIT. See LICENSE file.