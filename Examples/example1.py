#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  raspend - Example
#  
#  License: MIT
#  
#  Copyright (c) 2020 Joerg Beckers

import datetime
import random
import requests
from requests.exceptions import HTTPError
import argparse
import getpass
import json

from raspend import RaspendApplication, ThreadHandlerBase, ScheduleRepetitionType

class DoorBell():
    def __init__(self, *args, **kwargs):
        self.doorBellState = "on"

    def switchDoorBell(self, onoff: "set to 'on' or 'off' without quotation marks"):
        if type(onoff) == str:
            self.doorBellState = "on" if onoff == "on" else "off"
        elif type(onoff) == int:
            self.doorBellState = "on" if onoff >= 1 else "off"
        else:
            raise TypeError("State must be 'int' or 'string'.")
        return self.doorBellState

    def getCurrentState(self):
        return self.doorBellState

class ReadOneWireTemperature(ThreadHandlerBase):
    def __init__(self, groupId, sensorId, oneWireSensorPath = ""):
        # A groupId for grouping the temperature sensors
        self.groupId = groupId
        # The name or Id of your sensor under which you would read it's JSON value
        self.sensorId = sensorId
        # The path of your sensor within your system
        self.oneWireSensorPath = oneWireSensorPath

    def prepare(self):
        if self.groupId not in self.sharedDict:
            self.sharedDict[self.groupId] = {}
        self.sharedDict[self.groupId][self.sensorId] = 0
        return

    def invoke(self):
        # If you use 1-Wire sensors like a DS18B20 you normally would read its w1_slave file like:
        # /sys/bus/w1/devices/<the-sensor's system id>/w1_slave
        temp = random.randint(18, 24)
        self.sharedDict[self.groupId][self.sensorId] = temp
        return

class PublishOneWireTemperatures(ThreadHandlerBase):
    def __init__(self, endPointURL, userName, password):
        self.endPoint = endPointURL
        self.userName = userName
        self.password = password

    def prepare(self):
        # Nothing to prepare so far.
        pass

    def invoke(self):
        try:
            data = json.dumps(self.sharedDict)
            response = requests.post(self.endPoint, data, auth=(self.userName, self.password))
            response.raise_for_status()
        except HTTPError as http_err:
            print("HTTP error occurred: {}".format(http_err))
        except Exception as err:
            print("Unexpected error occurred: {}".format(err))
        else:
            print(response.text)

class WriteOneWireTemperaturesToFile(ThreadHandlerBase):
        def __init__(self, fileName):
            self.fileName = fileName
            return

        def prepare(self):
            #  Here we could check, if the given file exists and if not create it.
            return

        def invoke(self):
            print ("{} - Writing temperatures to '{}'.".format(datetime.datetime.now().isoformat(), self.fileName))
            return

def main():

    cmdLineParser = argparse.ArgumentParser(prog="example1", usage="%(prog)s [options]")
    cmdLineParser.add_argument("--port", help="The port the server should listen on", type=int, required=True)

    try: 
        args = cmdLineParser.parse_args()
    except SystemExit:
        return

    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    myApp = RaspendApplication(args.port)

    theDoorBell = DoorBell()

    myApp.addCommand(theDoorBell.switchDoorBell)
    myApp.addCommand(theDoorBell.getCurrentState)

    myApp.updateSharedDict({"Starting Time" : datetime.datetime.now().isoformat()})
    
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
    
    myApp.run()

    print ("Exit")

if __name__ == "__main__":
    main()