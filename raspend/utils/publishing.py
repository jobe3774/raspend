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

class ScheduledPublishDataThread(PublishDataThread):
    def __init__(self, 
                 startTime: "A 2-tuple containing starting hour and minute", 
                 repetionFlag: "'w' (weekly), 'd' (daily), 'h' (hourly)", 
                 shutdownFlag = None, dataLock = None, publishDataHandler = None):

        if repetionFlag.lower() not in "wdh":
            raise ValueError("'repetionFlag' must be 'w' (weekly), 'd' (daily) or 'h' (hourly)")

        self.startTime = startTime
        self.repetionFlag = repetionFlag

        return super().__init__(0, shutdownFlag, dataLock, publishDataHandler)

    def getTimedeltaFactors(self):
        if self.repetionFlag == "w":
            weekly = 1
        else:
            weekly = 0

        if self.repetionFlag == "d":
            daily = 1
        else:
            daily = 0

        if self.repetionFlag == "h":
            hourly = 1
        else:
            hourly = 0

        return weekly, daily, hourly

    def run(self):
        """ The thread loop runs until 'shutdownFlag' has been signaled. 
        """
        # Let the handler prepare itself if necessary.
        self.dataLock.acquire()
        self.publishDataHandler.prepare()
        self.dataLock.release()
        
        weekly, daily, hourly = self.getTimedeltaFactors()

        # Calculate the initial timeout, which is the number of seconds from now to start time.
        tNow = datetime.now()
        t0 = datetime(tNow.year, tNow.month, tNow.day, self.startTime[0], self.startTime[1], 0, 0)

        timeout = (t0 - tNow).total_seconds()

        # If timeout is negativ, then we already passed start time. 
        # In that case we calculate the timeout for the coming iteration.
        if timeout < 0.0:
            t1 = t0 + timedelta(days = 1 * daily, weeks = 1 * weekly, hours = 1 * hourly)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1

        while not self.shutdownFlag.wait(timeout):
            # acquire lock
            self.dataLock.acquire()
            # call publish data handler
            self.publishDataHandler.publishData()
            # release lock
            self.dataLock.release()

            t1 = t0 + timedelta(days = 1 * daily, weeks = 1 * weekly, hours = 1 * hourly)
            timeout = (t1 - datetime.now()).total_seconds()
            t0 = t1
        