# SPDX-License-Identifier: GPL-2.0-or-later
#
#   rteval_testserver.py
#   Local XML-RPC test server.  Can be used to verify XML-RPC behavoiur
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import os
import sys
import signal
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import argparse

import xmlrpc_API1
from Logger import Logger

# Default values
LISTEN="127.0.0.1"
PORT=65432

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/rteval/API1/',)


class RTevald_config(object):
    def __init__(self):
        self.config = {'datadir': '/tmp/rteval-xmlrpc-testsrv',
                       'db_server': 'localhost',
                       'db_port': 5432,
                       'database': 'dummy',
                       'db_username': None,
                       'db_password': None}
        self.__update_vars()

    def __update_vars(self):
        for k in list(self.config.keys()):
            self.__dict__[k] = self.config[k]


class RTevald():
    def __init__(self, options, log):
        self.options = options
        self.log = log
        self.server = None
        self.config = RTevald_config()

    def __prepare_datadir(self):
        startdir = os.getcwd()
        for dir in self.config.datadir.split("/"):
            if dir is '':
                continue
            if not os.path.exists(dir):
                os.mkdir(dir, 0o700)
            os.chdir(dir)
        if not os.path.exists('queue'):
            os.mkdir('queue', 0o700)
        os.chdir(startdir)

    def StartServer(self):
        # Create server
        self.server = SimpleXMLRPCServer((self.options.listen, self.options.port),
                                         requestHandler=RequestHandler)
        self.server.register_introspection_functions()

        # setup a class to handle requests
        self.server.register_instance(xmlrpc_API1.XMLRPC_API1(self.config, nodbaction=True, debug=True))

        # Run the server's main loop
        self.log.Log("StartServer", "Listening on %s:%i" % (self.options.listen, self.options.port))
        try:
            self.__prepare_datadir()
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.log.Log("StartServer", "Server caught SIGINT")
            self.server.shutdown()
        finally:
            self.log.Log("StartServer", "Server stopped")

    def StopServer(self):
        self.server.shutdown()


logger = None
rtevalserver = None

#
#  M A I N   F U N C T I O N
#

if __name__ == '__main__':
    parser = argparse.ArgumentParser(version="%prog v0.1")

    parser.add_argument("-L", "--listen", action="store", dest="listen", default=LISTEN,
                      help="Which interface to listen to [default: %default]", metavar="IPADDR")
    parser.add_argument("-P", "--port", action="store", type="int", dest="port", default=PORT,
                      help="Which port to listen to [default: %default]",  metavar="PORT")
    parser.add_argument("-l", "--log", action="store", dest="logfile", default=None,
                      help="Where to log requests.", metavar="FILE")

    options = parser.parse_args()

    logger = Logger(options.logfile, "RTeval")
    rtevalserver = RTevald(options, logger)
    rtevalserver.StartServer()
