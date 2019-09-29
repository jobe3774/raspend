#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This module contains classes for invoking class methods by their names. 
#  For example, it allows you to make these methods available to the outside 
#  world via a network interface. 
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import json
import inspect

class CallbackFunction():
    """
    This class holds a reference to a method of an object.
    
    Usage: 

    obj = classObject()
    cb  = Callback(obj.anyMethod)

    args = dict()

    args["arg1"] = 1
    args["arg2"] = 2

    cb.invoke(args)

    """

    def __init__(self, callbackFunction):
        self.__function = callbackFunction
        self.__name = callbackFunction.__name__
        self.__signature = inspect.signature(callbackFunction)
        self.__objName = self.__findObjectName()

    def __findObjectName(self):
        """
        Determines the variable name of the object whose method was supplied to this instance of class 'CallbackFunction'.
        """
        objToFind = self.__function.__self__
        currStack = inspect.stack()
        for stackFrame in currStack[2:]:
            # Make a copy of the keys to prevent runtime errors because of changes to the dictionary during iteration.
            frameLocalVarNames = list(stackFrame.frame.f_locals)
            for varName in frameLocalVarNames:
                obj = stackFrame.frame.f_locals[varName]
                if obj == objToFind:
                    return varName
        return ""

    def getName(self):
        """
        Returns the name of this instance of class 'CallbackFunction', which is the variable name of the object whose method
        was supplied to this instance and the name of the method itself divided by a period.
        """
        if len(self.__objName):
            return self.__objName + "." + self.__name
        else:
            # We should never come here!
            return self.__function.__qualname__

    def hasParameter(self, parameterName):
        """
        Checks if the signature of the supplied callback method contains 'parameterName'.
        """
        return parameterName in self.__signature.parameters.keys()

    def getParameters(self):
        """
        Returns a dictionary containing the arguments of the supplied callback method.
        """
        return self.__signature.parameters;

    def invoke(self, args):
        """
        Check args and invoke callback method.
        """
        if not type(args) is dict:
            raise TypeError("Arguments need to be passed in a dictionary!")
        for key in args.keys():
            if not self.hasParameter(key):
                raise KeyError("No argument '{0}' found!".format(key))
        return self.__function(**args)

class Command():
    """
    This class wraps a 'CallbackFunction' object.
    """

    def __init__(self, callback):
        self.__callback = CallbackFunction(callback)
        self.__name = self.__callback.getName()

    def getName(self):
        """
        Returns the full name of callback wrapped by this instance.
        """
        return self.__name

    def describe(self, asJSON):
        """
        Returns either a JSON string describing this instance or a dictionary.
        """
        d = dict()
        d["Command"] = dict()
        d["Command"]["Name"] = self.__name
        d["Command"]["Args"] = dict()
        params = self.__callback.getParameters()
        for p in params:
            param = params[p]
            d["Command"]["Args"][param.name] = param.annotation if param.annotation != inspect.Parameter.empty else ""
        if asJSON == True:
            return json.dumps(d, ensure_ascii=False)
        else:
            return d

    def execute(self, args):
        """
        Accepts a dictionary containing the arguments for the callback function. 'key' is an argument's name and 'value' is the value.
        """
        return self.__callback.invoke(args)

class CommandMap(dict):
    """
    A dictionary for holding instances of class 'Command'.
    """

    def __init__(self):
        return super().__init__()

    def add(self, Command):
        """
        Adds 'Command' by its name to the dictionary.
        """
        self[Command.getName()] = Command
