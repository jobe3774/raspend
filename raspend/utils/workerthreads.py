#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Classes to simplify multithreading.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime, date, time, timedelta

class ThreadHandlerBase(ABC):
    """ This abstract class describes the basic structure of a raspend thread handler.
        Derive this class and implement the 'prepare' and 'invoke' methods.
        'prepare' is called prior to running the thread's loop and 'invoke' is called 
        for every loop iteration. Every thread and therefore every handler instance
        uses the same shared dictionary to read and write it's data. 
    """
    def __init__(self, sharedDict=None):
        self.setSharedDict(sharedDict)
        return super().__init__()

    def setSharedDict(self, sharedDict):
        """ Sets the shared dictionary.
        """
        self.sharedDict = sharedDict

    @abstractmethod
    def prepare(self):
        """ This method is called prior to running the thread's loop.
        """
        pass

    @abstractmethod
    def invoke(self):
        """ This method is called for every loop iteration.
        """
        pass

class WorkerThreadBase(ABC, threading.Thread):
    """ The base class for every worker thread.
    """
    def __init__(self, shutdownEvent, accessLock, threadHandler):
        """ Parameters:
            shutdownEvent - an 'Event' object for gracefully shutting down this thread.
            accessLock - a 'Lock' object for synchronizing access to the thread handler.
            threadHandler - an instance of a class deriving 'ThreadHandlerBase'.
        """
        threading.Thread.__init__(self)
        self.shutdownEvent = shutdownEvent
        self.accessLock = accessLock
        if not isinstance(threadHandler, ThreadHandlerBase):
            raise TypeError("'threadHandler' must be a derivative of 'ThreadHandlerBase'.")
        self.threadHandler = threadHandler
        return

    @abstractmethod
    def run(self):
        pass

class WorkerThread(WorkerThreadBase):
    """ A worker thread. It sleeps for 'waitTimeout' seconds before doing the next iteration.
        The run - loop runs until 'shutdownEvent' has been signaled.
    """
    def __init__(self, shutdownEvent, accessLock, threadHandler, waitTimeout):
        super().__init__(shutdownEvent, accessLock, threadHandler)
        self.waitTimeout = waitTimeout
        return

    def run(self):
        self.accessLock.acquire()
        self.threadHandler.prepare()
        self.accessLock.release()

        while not self.shutdownEvent.is_set():
            self.accessLock.acquire()
            self.threadHandler.invoke()
            self.accessLock.release()
            self.shutdownEvent.wait(self.waitTimeout)
        return

class ScheduleRepetitionType(Enum):
    """ Constants describing the repetition rate of a scheduled worker thread.
    """
    WEEKLY = 1
    DAILY = 2
    HOURLY = 3
    MINUTELY = 4
    SECOND = 5

class ScheduledWorkerThread(WorkerThreadBase):
    """ A worker thread using a schedule date and time for doing an iteration.
        'repetitionType' and 'repetitionFactor' describe the frequency iterations take place.
    """
    def __init__(self, shutdownEvent, accessLock, threadHandler, scheduledTime=None, scheduledDate=None, repetitionType=None, repetitionFactor=1):
        super().__init__(shutdownEvent, accessLock, threadHandler)
        
        if scheduledTime is None:
            scheduledTime = datetime.now().time()

        if scheduledDate is None:
            scheduledDate = datetime.now().date()

        self.scheduledStart = datetime.combine(scheduledDate, scheduledTime)

        if repetitionType and not isinstance(repetitionType, ScheduleRepetitionType):
            raise TypeError("'repetionType' must be of type 'ScheduleRepetitionType' or None.")
        elif repetitionType is None:
            repetitionType = ScheduleRepetitionType.DAILY

        if repetitionFactor < 1:
            raise ValueError("'repetitionFactor' must be 1 or greater.")

        self.repetitionType = repetitionType
        self.repetitionFactor = repetitionFactor
        return

    def getTimedeltaFactors(self):
        weeks = days = hours = minutes = seconds = 0
        if self.repetitionType == ScheduleRepetitionType.WEEKLY:
            weeks = self.repetitionFactor
        if self.repetitionType == ScheduleRepetitionType.DAILY:
            days = self.repetitionFactor
        if self.repetitionType == ScheduleRepetitionType.HOURLY:
            hours = self.repetitionFactor
        if self.repetitionType == ScheduleRepetitionType.MINUTELY:
            minutes = self.repetitionFactor
        if self.repetitionType == ScheduleRepetitionType.SECOND:
            seconds = self.repetitionFactor
        return weeks, days, hours, minutes, seconds

    def run(self):
        self.accessLock.acquire()
        self.threadHandler.prepare()
        self.accessLock.release()

        weeks, days, hours, minutes, seconds = self.getTimedeltaFactors()

        tNow = datetime.now()
        t0 = self.scheduledStart
        timeout = (t0 - tNow).total_seconds()

        # If timeout is negative, then we already passed start time. 
        # In that case we calculate the timeout for the coming iteration.
        while timeout < 0.0:
            t1 = t0 + timedelta(days = days, weeks = weeks, hours = hours, minutes = minutes, seconds = seconds)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1

        while not self.shutdownEvent.wait(timeout):
            self.accessLock.acquire()
            self.threadHandler.invoke()
            self.accessLock.release()

            t1 = t0 + timedelta(days = days, weeks = weeks, hours = hours, minutes = minutes, seconds = seconds)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1
        return
