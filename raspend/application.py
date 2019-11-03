#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  
#  Main loop of an Raspend application.
#
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading
import time

from .http import RaspendHTTPServerThread
from .utils import serviceshutdownhandling as ServiceShutdownHandling
from .utils import dataacquisition as DataAcquisition
from .utils import commandmapping as CommandMapping
from .utils import publishing as Publishing
from .utils import workerthreads as WorkerThreads

class RaspendApplication():
    """ This class handles the main loop for a raspend based application.
    """

    def __init__(self, port=None, sharedDict=None):
        # The server port
        self.__port = port

        # A list holding instances of worker threads.
        self.__workers = list()

        # The dictionary holding user's commands he wants to expose.
        self.__cmdMap = CommandMapping.CommandMap()

        # A shared dictionary for the data acquisition threads and the HTTP server thread.
        if not sharedDict is None:
            self.__sharedDict = sharedDict
        else:
            self.__sharedDict = dict()
        
        # Event used for proper shutting down our threads.
        self.__shutdownFlag = threading.Event()
        
        # A lock object for synchronizing access to data within acquistion handlers and the HTTP request handler.
        self.__dataLock = threading.Lock()
        
    def createDataAcquisitionThread(self, dataAcquisitionHandler, threadSleep=1):
        """ This method creates a new instance of 'DataAcquisition.DataAcquisitionThread'.
            Make sure that the handler you provide is derived from 'DataAcquisition.DataAcquisitionHandler'!
        """
        if not isinstance(dataAcquisitionHandler, DataAcquisition.DataAcquisitionHandler):
            raise TypeError("Your 'DataAcquisitionHandler' must be derived from 'DataAcquisition.DataAcquisitionHandler'!")
        
        dataAcquisitionHandler.setSharedDict(self.__sharedDict)

        dataThread = DataAcquisition.DataAcquisitionThread(threadSleep, 
                                                           self.__shutdownFlag, 
                                                           self.__dataLock, 
                                                           dataAcquisitionHandler)
        self.__workers.append(dataThread)

        return len(self.__workers)

    def createPublishDataThread(self, publishDataHandler, threadSleep=1):
        """ This method creates a new instance of 'Publishing.PublishDataThread'.
            Make sure that the handler you provide is derived from 'Publishing.PublishDataHandler'!
        """
        if not isinstance(publishDataHandler, Publishing.PublishDataHandler):
            raise TypeError("Your 'PublishDataHandler' must be derived from 'Publishing.PublishDataHandler'!")
        
        publishDataHandler.setSharedDict(self.__sharedDict)

        publishDataThread = Publishing.PublishDataThread(threadSleep, 
                                                         self.__shutdownFlag, 
                                                         self.__dataLock, 
                                                         publishDataHandler)
        self.__workers.append(publishDataThread)

        return len(self.__workers)

    def createScheduledPublishDataThread(self, publishDataHandler, scheduledStartTime, repetionType):
        """ This method creates a new instance of 'Publishing.ScheduledPublishDataThread'.
            Make sure that the handler you provide is derived from 'Publishing.PublishDataHandler'!
        """
        if not isinstance(publishDataHandler, Publishing.PublishDataHandler):
            raise TypeError("Your 'PublishDataHandler' must be derived from 'Publishing.PublishDataHandler'!")
        
        publishDataHandler.setSharedDict(self.__sharedDict)

        scheduledPublishDataThread = Publishing.ScheduledPublishDataThread(scheduledStartTime, 
                                                                           repetionType, 
                                                                           self.__shutdownFlag, 
                                                                           self.__dataLock, 
                                                                           publishDataHandler)
        self.__workers.append(scheduledPublishDataThread)

        return len(self.__workers)

    def createWorkerThread(self, threadHandler, waitTimeout):
        if not isinstance(threadHandler, WorkerThreads.ThreadHandlerBase):
            raise TypeError("Your 'threadHandler' must be derived from 'WorkerThreads.ThreadHandlerBase'!")

        threadHandler.setSharedDict(self.__sharedDict)
        worker = WorkerThreads.WorkerThread(self.__shutdownFlag, self.__dataLock, threadHandler, waitTimeout)
        self.__workers.append(worker)
        return len(self.__workers)

    def createScheduledWorkerThread(self, threadHandler, scheduledTime, scheduledDate=None, repetitionType=None, repetitionFactor=1):
        if not isinstance(threadHandler, WorkerThreads.ThreadHandlerBase):
            raise TypeError("Your 'threadHandler' must be derived from 'WorkerThreads.ThreadHandlerBase'!")

        threadHandler.setSharedDict(self.__sharedDict)
        worker = WorkerThreads.ScheduledWorkerThread(self.__shutdownFlag, 
                                                     self.__dataLock, 
                                                     threadHandler, 
                                                     scheduledTime, 
                                                     scheduledDate, 
                                                     repetitionType, 
                                                     repetitionFactor)
        self.__workers.append(worker)
        return len(self.__workers)

    def addCommand(self, callbackMethod):
        """ Adds a new command to the command map of your application.
        """
        self.__cmdMap.add(CommandMapping.Command(callbackMethod))

        return len(self.__cmdMap)

    def updateSharedDict(self, other):
        """ Updates the shared dictionary with 'other'. 
            Note: existing keys will be overwritten!
        """
        self.__sharedDict.update(other)
        return len(self.__sharedDict)

    def run(self):
        """ Run the main loop of your application.
        """
        try:
            # Initialize signal handler to be able to have a graceful shutdown.
            ServiceShutdownHandling.initServiceShutdownHandling()

            httpd = None
            # The HTTP server thread - our HTTP interface
            if self.__port != None:
                httpd = RaspendHTTPServerThread(self.__shutdownFlag, self.__dataLock, self.__sharedDict, self.__cmdMap, self.__port)
                # Start our threads.
                httpd.start()

            for worker in self.__workers:
                worker.start()

            # Keep primary thread or main loop alive.
            while True:
                time.sleep(0.5)

        except ServiceShutdownHandling.ServiceShutdownException:
            # Signal the shutdown flag, so the threads can quit their work.
            self.__shutdownFlag.set()

            # Wait for all threads to end.
            for worker in self.__workers:
                worker.join()

            if httpd:
                httpd.join()

        except Exception as e:
            print ("An unexpected error occured. Error: {}".format(e))

        finally:
            pass

        return
