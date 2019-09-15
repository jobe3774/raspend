#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Encapsulates signal handling for graceful shutdown of an application.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import signal

class ServiceShutdownException(Exception):
    pass

def serviceShutdownHandler(signum, frame):
    raise ServiceShutdownException

def initServiceShutdownHandling():
    signal.signal(signal.SIGTERM, serviceShutdownHandler)
    signal.signal(signal.SIGINT, serviceShutdownHandler)