#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Simple classes that handle threaded data publishing.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading
import time

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
