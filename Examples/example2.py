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

class myDataAcquisitionHandler(DataAcquisition.DataAcquisitionHandler):
    def __init__(self, name, dataDict = None):
        self.name = name
        return super().__init__(dataDict)

    def acquireData(self):
        if not self.name in self.dataDict:
            self.dataDict[self.name] = {"loop" : 1}
        else:
            self.dataDict[self.name]["loop"] += 1

def main():
    logging.basicConfig(filename='raspend_example.log', level=logging.INFO)

    startTime = time.asctime()
    pid = os.getpid()

    logging.info("Starting at {} (PID={})".format(startTime, pid))

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

        # This handler is called by the data acquisition thread. 
        # Here you fill 'dataDict' with the data you want to expose via HTTP as a JSON string.
        # Make sure your data is serializable, otherwise the request handler will fail.
        dataGetter1 = myDataAcquisitionHandler(dataDict)
        dataGetter2 = myDataAcquisitionHandler(dataDict)
    
        # Start threads for acquiring some data.
        dataThread1 = DataAcquisition.DataAcquisitionThread(3, shutdownFlag, dataLock, dataGetter1)
        dataThread2 = DataAcquisition.DataAcquisitionThread(5, shutdownFlag, dataLock, dataGetter2)

        # The HTTP server thread - our HTTP interface
        httpd = RaspendHTTPServerThread(shutdownFlag, dataLock, dataDict, None, args.port)

        # Start our threads.
        dataThread1.start()
        dataThread2.start()
        httpd.start()

        # Keep primary thread alive.
        while True:
            time.sleep(0.5)

    except ServiceShutdownHandling.ServiceShutdownException:
        # Signal the shutdown flag, so the threads can quit their work.
        shutdownFlag.set()
        print ("Shutting down...")
        # Wait for all thread to end.
        dataThread1.join()
        dataThread2.join()
        httpd.join()

    except Exception as e:
        print ("An unexpected error occured. See 'raspend_example.log' for more information.")
        logging.exception("Unexpected error occured!", exc_info = True)

    finally:
        pass

    print ("Exit")

if __name__ == "__main__":
    main()