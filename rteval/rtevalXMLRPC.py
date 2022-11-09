# rtevalXMLRPC.py - main rteval XML-RPC class
#
#   Copyright 2009 - 2013   Clark Williams <williams@redhat.com>
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#   For the avoidance of doubt the "preferred form" of this code is one which
#   is in an open unpatent encumbered format. Where cryptographic key signing
#   forms part of the process of creating an executable the information
#   including keys needed to generate an equivalently functional executable
#   are deemed to be part of the source code.
#

import socket
import time
import xmlrpc.client
from .rtevalclient import rtevalclient
from .Log import Log

class rtevalXMLRPC:
    def __init__(self, host, logger, mailer=None):
        self.__host = host
        self.__url = f"http://{self.__host}/rteval/API1/"
        self.__logger = logger
        self.__mailer = mailer
        self.__client = rtevalclient.rtevalclient(self.__url)


    def Ping(self):
        res = None
        self.__logger.log(Log.DEBUG, f"Checking if XML-RPC server '{self.__host}' is reachable")
        attempt = 0
        ping_success = False
        warning_sent = False
        while attempt < 6:
            try:
                res = self.__client.Hello()
                attempt = 10
                ping_success = True
            except xmlrpc.client.ProtocolError:
                # Server do not support Hello(), but is reachable
                self.__logger.log(Log.INFO, f"Got XML-RPC connection with {self.__host} but it did not support Hello()")
                res = None
            except socket.error as err:
                self.__logger.log(Log.INFO, f"Could not establish XML-RPC contact with {self.__host}\n{str(err)}")

                # Do attempts handling
                attempt += 1
                if attempt > 5:
                    break # To avoid sleeping before we abort

                if (self.__mailer is not None) and (not warning_sent):
                    self.__mailer.SendMessage("[RTEVAL:WARNING] Failed to ping XML-RPC server", f"Server {self.__host} did not respond.")
                    warning_sent = True

                print(f"Failed pinging XML-RPC server.  Doing another attempt({attempt}) ")
                time.sleep(attempt) #*15) # Incremental sleep - sleep attempts*15 seconds
                ping_success = False

        if res:
            self.__logger.log(Log.INFO, f'Verified XML-RPC connection with {res["server"]} (XML-RPC API version: {res["APIversion"]})')
            self.__logger.log(Log.DEBUG, f"Recieved greeting: {res['greeting']}")
        return ping_success


    def SendReport(self, xmlreport):
        "Sends the report to a given XML-RPC host.  Returns 0 on success or 2 on submission failure."

        attempt = 0
        exitcode = 2   # Presume failure
        warning_sent = False
        while attempt < 6:
            try:
                print(f"Submitting report to {self.__url}")
                rterid = self.__client.SendReport(xmlreport)
                print(f"Report registered with submission id {rterid}")
                attempt = 10
                exitcode = 0 # Success
            except socket.error:
                attempt += 1
                if attempt > 5:
                    break # To avoid sleeping before we abort

                if (self.__mailer is not None) and (not warning_sent):
                    self.__mailer.SendMessage("[RTEVAL:WARNING] Failed to submit report to XML-RPC server", f"Server {self.__host} did not respond.  Not giving up yet.")
                    warning_sent = True

                print(f"Failed sending report. Making another attempt({attempt}) ")
                time.sleep(attempt) #*5*60) # Incremental sleep - sleep attempts*5 minutes

            except Exception as err:
                raise err


        if self.__mailer is not None:
            # Send final result messages
            if exitcode == 2:
                self.__mailer.SendMessage("[RTEVAL:FAILURE] Failed to submit report to XML-RPC server", f"Server {self.__host} did not respond at all after {attempt - 1} attempts.")
            elif (exitcode == 0) and warning_sent:
                self.__mailer.SendMessage("[RTEVAL:SUCCESS] XML-RPC server available again",
                                          f"Succeeded to submit the report to {self.__host}")

        return exitcode
