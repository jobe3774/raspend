#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Simple classes that handle threaded data publishing.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading
from datetime import datetime, timedelta
from enum import Enum
from collections import namedtuple

class PublishDataHandler():
    """ Base class for a handler which published data or parts of data store in the shared dictionary.
        Derive this class and override the 'publishData' - methods to publish the 'sharedDict'.
    """
    
    def __init__(self, sharedDict=None):
        """ The contructor gets a dictionary containing any acquired data of your application.
        """
        self.setSharedDict(sharedDict)

    def setSharedDict(self, sharedDict):
        """ Set the shared dictionary
        """
        self.sharedDict = sharedDict

    def prepare(self):
        """ This method is called before the publish thread is started with this handler.
            So if you need to initialize parts of the shared dictionary you should override this method.
        """
        pass

    def publishData(self):
        """ This method is called by a 'PublishDataThread'. Override this method publish your data in 'sharedDict'.
        """
        pass

class PublishDataThread(threading.Thread):
    """ A thread class which handles cyclic data publishing.

        An instance of this class needs a lock - object for controlling access to its 'publishDataHandler', an event - object for 
        notifying the thread to exit and an object of a class derived from 'PublishDataHandler'.
    """
    def __init__(self, threadSleep=0, shutdownFlag=None, dataLock=None, publishDataHandler=None):
        """ Contructs a new instance of 'PublishDataThread'.
            
            Parameters:
            
            threadSleep         - milliseconds sleep time for the thread loop.
            shutdownFlag        - a threading.event() object for notifying the thread to exit.
            dataLock            - a threading.Lock() object for controlling access to the 'dataAcquisitionHandler'.
            publishDataHandler  - an object of a class derived from 'PublishDataHandler'.
        """
        threading.Thread.__init__(self)

        self.threadSleep = threadSleep
        self.shutdownFlag = shutdownFlag
        self.dataLock = dataLock
        self.publishDataHandler = publishDataHandler
        
    def run(self):
        """ The thread loop runs until 'shutdownFlag' has been signaled. Sleep for 'threadSleep' milliseconds.
        """
        # Let the handler prepare itself if necessary.
        self.dataLock.acquire()
        self.publishDataHandler.prepare()
        self.dataLock.release()

        while not self.shutdownFlag.is_set():
            # acquire lock
            self.dataLock.acquire()
            # call publish data handler
            self.publishDataHandler.publishData()
            # release lock
            self.dataLock.release()
            self.shutdownFlag.wait(self.threadSleep)

class RepetitionType(Enum):
    WEEKLY = 1
    DAILY = 2
    HOURLY = 3
    MINUTELY = 4

ScheduledStartTime = namedtuple("ScheduledStartTime", "hour minute second")

class ScheduledPublishDataThread(PublishDataThread):
    def __init__(self, 
                 scheduledStartTime, 
                 repetionType, 
                 shutdownFlag = None, dataLock = None, publishDataHandler = None):

        if not isinstance(repetionType, RepetitionType):
            raise ValueError("'repetionType' must be of type 'RepetitionType'.")

        if not isinstance(scheduledStartTime, ScheduledStartTime):
            raise ValueError("'scheduledStartTime' must be of type 'ScheduledStartTime'.")

        self.scheduledStartTime = scheduledStartTime
        self.repetionType = repetionType

        return super().__init__(0, shutdownFlag, dataLock, publishDataHandler)

    def getTimedeltaFactors(self):
        weekly = daily = hourly = minutely = 0
        if self.repetionType == RepetitionType.WEEKLY:
            weekly = 1
        if self.repetionType == RepetitionType.DAILY:
            daily = 1
        if self.repetionType == RepetitionType.HOURLY:
            hourly = 1
        if self.repetionType == RepetitionType.MINUTELY:
            minutely = 1
        return weekly, daily, hourly, minutely

    def run(self):
        """ The thread loop runs until 'shutdownFlag' has been signaled. 
        """
        # Let the handler prepare itself if necessary.
        self.dataLock.acquire()
        self.publishDataHandler.prepare()
        self.dataLock.release()
        
        weekly, daily, hourly, minutely = self.getTimedeltaFactors()

        # Calculate the initial timeout, which is the number of seconds from now to start time.
        tNow = datetime.now()
        t0 = datetime(tNow.year, tNow.month, tNow.day, self.scheduledStartTime.hour, self.scheduledStartTime.minute, self.scheduledStartTime.second)

        timeout = (t0 - tNow).total_seconds()

        # If timeout is negativ, then we already passed start time. 
        # In that case we calculate the timeout for the coming iteration.
        while timeout < 0.0:
            t1 = t0 + timedelta(days = 1 * daily, weeks = 1 * weekly, hours = 1 * hourly, minutes = 1 * minutely)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1

        while not self.shutdownFlag.wait(timeout):
            # acquire lock
            self.dataLock.acquire()
            # call publish data handler
            self.publishDataHandler.publishData()
            # release lock
            self.dataLock.release()

            t1 = t0 + timedelta(days = 1 * daily, weeks = 1 * weekly, hours = 1 * hourly, minutes = 1 * minutely)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1
        