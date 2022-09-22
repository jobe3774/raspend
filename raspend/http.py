#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  The HTTP request handling interface for raspend.
#  'raspend' stands for RaspberryPi Backend.
#  
#  License: MIT
#  
#  Copyright (c) 2020 Joerg Beckers

from functools import partial
from http.server import BaseHTTPRequestHandler
import json
import urllib

from .utils import stoppablehttpserver


class RaspendHttpRequestHandler(BaseHTTPRequestHandler):
    """ This class handles all incoming request to the raspend server
    """
    def __init__(self, dataLock, sharedDict, commandMap, *args, **kwargs):
        self.dataLock = dataLock
        self.sharedDict = sharedDict
        self.commandMap = commandMap
        return super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """ Handle browsers preflight-request to allow POST.
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')                
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        self.send_header("Access-Control-Allow-Headers", 'Origin, Content-Type, Accept, Authorization, X-Request-With') 
        self.end_headers()
        return

    def verifyContentType(self, desiredType, desiredCharset=""):
        """ Check if 'Content-Type' contains what we want.
        """
        content_type = self.headers.get('Content-Type')
        
        if content_type == None:
            return False
        
        parts = content_type.split(";")
        mediatype = parts[0]
        charset = parts[1] if len(parts) > 1 else ""
        
        isDesiredMediaType = True if mediatype.lower() == desiredType.lower() else False

        if len(desiredCharset):
            isDesiredCharset = True if desiredCharset.lower() in charset.lower() else False
        else:
            isDesiredCharset = True
        
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

        if self.verifyContentType("application/json") == False:
            self.send_error(415, "Invalid media type! Expecting 'application/json'.")
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
        """ Called when / is requested and dumps the given 'sharedDict' completly.
        """
        self.dataLock.acquire()
        strJsonResponse = json.dumps(self.sharedDict, ensure_ascii=False)
        self.dataLock.release()
        return strJsonResponse
                
    def onGetDetailedDataPath(self):
        """ Called when a more detailed path is requested. This allows you to request sub-elements of 'sharedDict'.
        """
        pathParts = self.path.split('/')
        self.dataLock.acquire()
        data = self.sharedDict
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
            desc = cmd.describe(False)
            cmdURL = "/cmd?name={}".format(desc["Command"]["Name"])
            for arg in desc["Command"]["Args"]:
                cmdURL = cmdURL + "&{}=".format(arg)
            desc["Command"]["URL"] = cmdURL
            cmds["Commands"].append(desc)

        strJsonResponse = json.dumps(cmds, ensure_ascii=False)

        self.dataLock.release()
        return strJsonResponse

    def onGetCmd(self, queryParams):
        """ Call a command via HTTP GET. The response will be the command's return value as a JSON string.
        """
        strJsonResponse = ""

        cmdName = queryParams["name"][0]
        cmdArgs = dict()

        cmd = self.commandMap.get(cmdName)

        if cmd == None:
            self.send_error(404, ("Command '{0}' not found!".format(cmdName)))
            return

        del (queryParams["name"])

        for k,v in queryParams.items():
            cmdArgs[k] = v[0]

        result = ""

        try:
            result = cmd.execute(cmdArgs)
        except Exception as e:
            self.send_error(500, "An unexpected error occured during execution of '{0}'! Exception: {1}".format(cmdName, e))
            return

        strJsonResponse = json.dumps(result, ensure_ascii=False)
            
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
        except Exception as e:
            self.send_error(500, "An unexpected error occured during execution of '{0}'! Exception: {1}".format(cmdName, e))
        return

    def do_GET(self):
        """ Handle HTTP GET request

            '/data'     : returns the whole 'sharedDict' as JSON string
            '/data/key' : returns sub-element of 'sharedDict' as JSON string
            '/cmds'     : returns the list of available commands
        """
        urlComponents = urllib.parse.urlparse(self.path)
        queryParams = urllib.parse.parse_qs(urlComponents.query)

        strJsonResponse = ""

        if urlComponents.path.lower() == "/cmds":
            if self.commandMap == None or len(self.commandMap) == 0:
                self.send_error(501, "No commands available")
                return
            else:
                strJsonResponse = self.onGetCmds()
        elif urlComponents.path.lower() == "/cmd":
            if self.commandMap == None or len(self.commandMap) == 0:
                self.send_error(501, "No commands available")
                return
            else:
                return self.onGetCmd(queryParams)
        elif urlComponents.path.lower() == "/data" and self.sharedDict != None:
            strJsonResponse = self.onGetRootDataPath()
        elif urlComponents.path.startswith("/data/")  and self.sharedDict != None:
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
    def __init__(self, shutdownFlag=None, dataLock=None, sharedDict=None, commandMap=None, serverPort=0):
        handler = partial(RaspendHttpRequestHandler, dataLock, sharedDict, commandMap)
        return super().__init__(shutdownFlag=shutdownFlag, handler=handler, serverPort=serverPort)
