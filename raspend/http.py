#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  The HTTP request handling interface for raspend.
#  'raspend' stands for RaspberryPi EndPoint.
#  
#  License: MIT
#  
#  Copyright (c) 2019 Joerg Beckers

from functools import partial
from http.server import BaseHTTPRequestHandler
import json

from .utils import stoppablehttpserver


class RaspendHttpRequestHandler(BaseHTTPRequestHandler):
    """ This class handles all incoming request to the raspend server
    """
    def __init__(self, dataLock, dataDict, commandMap, *args, **kwargs):
        self.dataLock = dataLock
        self.dataDict = dataDict
        self.commandMap = commandMap
        return super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """ Handle browsers preflight-request to allow POST.
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')                
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type") 
        self.end_headers()
        return

    def verifyContentType(self, desiredType, desiredCharset):
        """ Check if 'Content-Type' contains what we want.
        """
        content_type = self.headers.get('Content-Type')
        
        if content_type == None:
            return False
        
        parts = content_type.split(";")
        mediatype = parts[0]
        charset = parts[1] if len(parts) > 1 else ""
        
        isDesiredMediaType = True if mediatype.lower() == desiredType.lower() else False
        isDesiredCharset   = True if desiredCharset.lower() in charset.lower() else False
        
        return isDesiredMediaType and isDesiredCharset

    def verifyPayload(self, payload):
        """ Verifies the format of the payload sent via HTTP POST. 
            As we are dealing with commands that can be invoked via POST, we need to make sure that payload contains what we expect.
        """
        if not type(payload) is dict:
            return False
        if not "Command" in payload.keys():
            return False
        if not "Name" in payload["Command"].keys():
            return False
        return True

    def do_POST(self):
        """ Handle HTTP POST request. Currently this only handles payloads containing a call to a command.
        
            The payload has the following format:
        
            A JavaScript example:
        
            let payLoad = {
                "Command" : {
                    "Name" : "testCmd.methodToCall",
                    "Args" : {
                        "arg1" : 5,
                        "arg2" : 23
                    }
                }
           };
        
           'args' is optional
        
           The payload will be enhanced with the result of the method invocation and returned via JSON to the caller. 
           So you have the opportunity to add any information to the payload e.g. an id of an front-end element connected 
           to the respective command.
        """
        if self.commandMap == None:
            self.send_error(501, "No commands available.")
            return

        if self.verifyContentType("application/json", "utf-8") == False:
            self.send_error(415, "Invalid media type! Expecting 'application/json' using character set 'utf-8'")
            return

        content_length = int(self.headers.get('Content-Length', 0))

        try:
            message_body = self.rfile.read(content_length)
        except BlockingIOError:
            self.send_error(500, "Could not read message body!")
            return

        try:
            payload = json.loads(message_body.decode('UTF-8'))
        except json.JSONDecodeError:
            self.send_error(500, "Encountered a JSON decoding error");
            return

        if self.verifyPayload(payload) == False:
            self.send_error(400, "Unable to verify payload!")
            return

        # Find command handler by its name and execute it with args if given
        
        cmd = self.commandMap.get(payload["Command"]["Name"])

        if cmd == None:
            self.send_error(404, "Command '{0}' not found!".format(payload["Command"]["Name"]))
            return

        args = dict()

        if "Args" in payload["Command"]:
            args = payload["Command"]["Args"]

        result = ""

        try:
            result = cmd.execute(args)
        except Exception as e:
            self.send_error(500, "An unexpected error occured during execution of '{0}'! Exception: {1}".format(payload["Command"]["Name"], e))
            return

        payload["Command"]["Result"] = result

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        self.wfile.write(bytes(json.dumps(payload, ensure_ascii=False), encoding = "UTF-8"))

        return

    def onGetRootDataPath(self):
        """ Called when / is requested and dumps the given 'dataDict' completly.
        """
        self.dataLock.acquire()
        strJsonResponse = json.dumps(self.dataDict, ensure_ascii=False)
        self.dataLock.release()
        return strJsonResponse
                
    def onGetDetailedDataPath(self):
        """ Called when a more detailed path is requested. This allows you to request sub-elements of 'dataDict'.
        """
        pathParts = self.path.split('/')
        self.dataLock.acquire()
        data = self.dataDict
        for part in pathParts[1:]:
            if type(data) is dict and part in data.keys():
                data = data[part]
        strJsonResponse = json.dumps(data, ensure_ascii=False)
        self.dataLock.release()
        return strJsonResponse

    def onGetCmds(self):
        """ Respond with a list of all known commands. Format is a JSON string.
        """
        strJsonResponse = ""
        self.dataLock.acquire()

        cmds = dict()
        cmds["Commands"] = []
        for cmd in self.commandMap.values():
            cmds["Commands"].append(cmd.describe(False))

        strJsonResponse = json.dumps(cmds, ensure_ascii=False)

        self.dataLock.release()
        return strJsonResponse

    def do_GET(self):
        """ Handle HTTP GET request

            '/data'     : returns the whole 'dataDict' as JSON string
            '/data/key' : returns sub-element of 'dataDict' as JSON string
            '/cmds'     : returns the list of available commands
        """
        strJsonResponse = ""
        
        if self.path.lower() == "/cmds":
            if self.commandMap == None or len(self.commandMap) == 0:
                self.send_error(501, "No commands available.")
            else:
                strJsonResponse = self.onGetCmds()
        elif self.path == "/data" and self.dataDict != None:
            strJsonResponse = self.onGetRootDataPath()
        elif self.path.startswith("/data/")  and self.dataDict != None:
            strJsonResponse = self.onGetDetailedDataPath()
        else:
            self.send_error(404)
            return

        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(bytes(strJsonResponse, 'utf-8'))
        except OSError:
            self.send_error(500)
        except BlockingIOError:
            self.send_error(500)

class RaspendHTTPServerThread(stoppablehttpserver.StoppableHttpServerThread):
    """ The raspend server thread using 'RaspendHttpRequestHandler' for request handling
    """
    def __init__(self, shutdownFlag=None, dataLock=None, dataDict=None, commandMap=None, serverPort=0):
        handler = partial(RaspendHttpRequestHandler, dataLock, dataDict, commandMap)
        return super().__init__(shutdownFlag=shutdownFlag, handler=handler, serverPort=serverPort)
