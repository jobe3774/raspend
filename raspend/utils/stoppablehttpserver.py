#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  A HTTP server thread that can be stopped by a supplied threading.event() object.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

import threading
import time
from http.server import HTTPServer
from socketserver import ThreadingMixIn

class StoppableHttpServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, shutdownFlag=None):
        super().__init__(server_address, RequestHandlerClass)
        self.shutdownFlag = shutdownFlag
        self.daemon_threads = False
        self._block_on_close = False

    def serve_forever(self):
        self.socket.settimeout(0.5)
        while not self.shutdownFlag.is_set():
            self.handle_request()
        self.server_close()

class StoppableHttpServerThread(threading.Thread):
    def __init__(self, 
                 shutdownFlag=None, 
                 handler=None,
                 serverPort=0):
        threading.Thread.__init__(self)

        self.shutdownFlag = shutdownFlag
        self.stoppableHttpServer = StoppableHttpServer(('', serverPort), handler, shutdownFlag)

    def run(self):
        self.stoppableHttpServer.serve_forever()