#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  raspend - Example
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import logging
import threading
import argparse
import time
import os

from raspend.http import RaspendHTTPServerThread
import raspend.utils.serviceshutdownhandling as ServiceShutdownHandling
import raspend.utils.dataacquisition as DataAcquisition
import raspend.utils.commandmapping as CommandMapping

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

def main():
    logging.basicConfig(filename='raspend_example.log', level=logging.INFO)

    startTime = time.asctime()
    pid = os.getpid()

    logging.info(f"Starting at {startTime} (PID={pid})")

    # Check commandline arguments.
    cmdLineParser = argparse.ArgumentParser(prog="raspend_example", usage="%(prog)s [options]")
    cmdLineParser.add_argument("--port", help="The port the server should listen on", type=int, required=True)

    try: 
        args = cmdLineParser.parse_args()
    except SystemExit:
        return

    try:
        # Initialize signal handler to be able to have a graceful shutdown.
        ServiceShutdownHandling.initServiceShutdownHandling()

        # Object for holding the data.
        dataDict = dict()

        # Event used for proper shutting down our threads.
        shutdownFlag = threading.Event()

        # A lock object for synchronizing access to data within acquistion handlers and the HTTP request handler.
        dataLock = threading.Lock()

        # Create some objects whose methods we want to expose via HTTP interface.
        theDoorBell = DoorBell()

        # Create a command map for the HTTP interface, so that it knows which commands are available for calling via HTTP POST request.
        # Use 'http://server:port/cmds' to get a list of commands as a JSON string.
        cmdMap = CommandMapping.CommandMap()

        # Add some methods to the command map.
        cmdMap.add(CommandMapping.Command(theDoorBell.switchDoorBell))
        cmdMap.add(CommandMapping.Command(theDoorBell.getCurrentState))

        # The HTTP server thread - our HTTP interface
        httpd = RaspendHTTPServerThread(shutdownFlag, dataLock, dataDict, cmdMap, args.port)

        # Start thread.
        httpd.start()

        # Keep primary thread alive.
        while True:
            time.sleep(0.5)

    except ServiceShutdownHandling.ServiceShutdownException:
        # Signal the shutdown flag, so the threads can quit their work.
        shutdownFlag.set()
        print ("Shutting down...")
        # Wait for thread to end.
        httpd.join()

    except Exception as e:
        print ("An unexpected error occured. See 'raspend_example.log' for more information.")
        logging.exception("Unexpected error occured!", exc_info = True)

    finally:
        pass

    print ("Exit")

if __name__ == "__main__":
    main()