#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  
#  Main loop of an Raspend application
#
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading

from .http import RaspendHTTPServerThread
from .utils import serviceshutdownhandling as ServiceShutdownHandling
from .utils import dataacquisition as DataAcquisition
from .utils import commandmapping as CommandMapping

class RaspendApplication():
    def __init__(self, *args, **kwargs):
        # A list holding instances of DataAcquisitionThread 
        self.daqThreads = list()
        # The dictionary holding users commands he wants to expose.
        self.cmdMap = CommandMapping.CommandMap()
        # A shared dictionary for the data acquisition threads and the HTTP server thread.
        self.dataDict = dict()
        # Event used for proper shutting down our threads.
        self.shutdownFlag = threading.Event()
        # A lock object for synchronizing access to data within acquistion handlers and the HTTP request handler.
        self.dataLock = threading.Lock()

    def createDataAcquisitionThread(self, dataAcquisitionHandler):
