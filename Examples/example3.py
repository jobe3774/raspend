#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  raspend - Example
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import random

from raspend.application import RaspendApplication
from raspend.utils import dataacquisition as DataAcquisition

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

theDoorBell = DoorBell()

myApp.addCommand(theDoorBell.switchDoorBell)
myApp.addCommand(theDoorBell.getCurrentState)

myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "party_room", "/sys/bus/w1/devices/23-000000000001/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "heating_room", "/sys/bus/w1/devices/23-000000000002/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("basement", "fitness_room", "/sys/bus/w1/devices/23-000000000003/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("ground_floor", "kitchen", "/sys/bus/w1/devices/23-000000000004/w1_slave"), 30)
myApp.createDataAcquisitionThread(ReadOneWireTemperature("ground_floor", "living_room", "/sys/bus/w1/devices/23-000000000005/w1_slave"), 30)

myApp.run()

print ("Exit")
