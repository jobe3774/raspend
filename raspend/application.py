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
from .utils import commandmapping as CommandMapping
from .utils import workerthreads as WorkerThreads

class RaspendApplication():
    """ This class handles the main loop for a raspend based application.
    """

    def __init__(self, port=None, sharedDict=None):
        # The server port
        self._port = port

        # A list holding instances of worker threads.
        self._workers = list()

        # The dictionary holding user's commands he wants to expose.
        self._cmdMap = CommandMapping.CommandMap()

        # A shared dictionary for the data acquisition threads and the HTTP server thread.
        if not sharedDict is None:
            self._sharedDict = sharedDict
        else:
            self._sharedDict = dict()
        
        # Event used for proper shutting down our threads.
        self._shutdownFlag = threading.Event()
        
        # A lock object for synchronizing access to data within acquistion handlers and the HTTP request handler.
        self._dataLock = threading.Lock()
        
    def createWorkerThread(self, threadHandler, waitTimeout):
        """ This method creates a 'normal' worker thread.
            Make sure your thread handler is derived from 'WorkerThreads.ThreadHandlerBase'.
        """
        if not isinstance(threadHandler, WorkerThreads.ThreadHandlerBase):
            raise TypeError("Your 'threadHandler' must be derived from 'WorkerThreads.ThreadHandlerBase'!")

        threadHandler.setSharedDict(self._sharedDict)
        threadHandler.setShutdownFlag(self._shutdownFlag)
        worker = WorkerThreads.WorkerThread(self._shutdownFlag, self._dataLock, threadHandler, waitTimeout)
        self._workers.append(worker)
        return len(self._workers)

    def createScheduledWorkerThread(self, threadHandler, scheduledTime, scheduledDate=None, repetitionType=None, repetitionFactor=1):
        """ This method creates a scheduled worker thread. It takes a start time and date. 
            Furthermore it takes a repetition type and factor to control by what frequency every iteration of the thread should be done.
            Make sure your thread handler is derived from 'WorkerThreads.ThreadHandlerBase'.
        """
        if not isinstance(threadHandler, WorkerThreads.ThreadHandlerBase):
            raise TypeError("Your 'threadHandler' must be derived from 'WorkerThreads.ThreadHandlerBase'!")

        threadHandler.setSharedDict(self._sharedDict)
        threadHandler.setShutdownFlag(self._shutdownFlag)
        worker = WorkerThreads.ScheduledWorkerThread(self._shutdownFlag, 
                                                     self._dataLock, 
                                                     threadHandler, 
                                                     scheduledTime, 
                                                     scheduledDate, 
                                                     repetitionType, 
                                                     repetitionFactor)
        self._workers.append(worker)
        return len(self._workers)

    def addCommand(self, callbackMethod):
        """ Adds a new command to the command map of your application.
        """
        self._cmdMap.add(CommandMapping.Command(callbackMethod))

        return len(self._cmdMap)

    def updateSharedDict(self, other):
        """ Updates the shared dictionary with 'other'. 
            Note: existing keys will be overwritten!
        """
        self._sharedDict.update(other)
        return len(self._sharedDict)

    def run(self):
        """ Run the main loop of your application.
        """
        try:
            # Initialize signal handler to be able to have a graceful shutdown.
            ServiceShutdownHandling.initServiceShutdownHandling()

            httpd = None
            # The HTTP server thread - our HTTP interface
            if self._port != None:
                httpd = RaspendHTTPServerThread(self._shutdownFlag, self._dataLock, self._sharedDict, self._cmdMap, self._port)
                # Start our threads.
                httpd.start()

            for worker in self._workers:
                worker.start()

            # Keep primary thread or main loop alive.
            while True:
                time.sleep(0.5)

        except ServiceShutdownHandling.ServiceShutdownException:
            # Signal the shutdown flag, so the threads can quit their work.
            self._shutdownFlag.set()

            # Wait for all threads to end.
            for worker in self._workers:
                worker.join()

            if httpd:
                httpd.join()

        except Exception as e:
            print ("An unexpected error occured. Error: {}".format(e))

        finally:
            pass

        return
