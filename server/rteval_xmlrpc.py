# SPDX-License-Identifier: GPL-2.0-or-later
#
#   rteval_xmlrpc.py
#   XML-RPC handler for mod_python which will receive requests
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import types
from mod_python import apache
from xmlrpc.client import dumps, loads, Fault
from xmlrpc_API1 import XMLRPC_API1
from rteval.rtevalConfig import rtevalConfig


def Dispatch(req, method, args):
    # Default configuration
    defcfg = {'xmlrpc_server': { 'datadir':     '/var/lib/rteval',
                                 'db_server':   'localhost',
                                 'db_port':     5432,
                                 'database':    'rteval',
                                 'db_username': 'rtevxmlrpc',
                                 'db_password': 'rtevaldb'
                                 }
              }

    # Fetch configuration
    cfg = rtevalConfig(defcfg)
    cfg.Load(append=True)

    # Prepare an object for executing the query
    xmlrpc = XMLRPC_API1(config=cfg.GetSection('xmlrpc_server'))

    # Exectute it
    result = xmlrpc.Dispatch(method, args)

    # Send the result
    if type(result) == tuple:
        req.write(dumps(result, None, methodresponse=1))
    else:
        req.write(dumps((result,), None, methodresponse=1))


def handler(req):
    # Only accept POST requests
    if req.method != 'POST':
        req.content_type = 'text/plain'
        req.send_http_header()
        req.write("Not valid XML-RPC POST request")
        return apache.OK

    # Fetch the request
    body = req.read()

    # Prepare response
    req.content_type = "text/xml"
    req.send_http_header()

    # Process request
    try:
        args, method = loads(body)
    except:
        fault = Fault(0x001, "Invalid XML-RPC error")
        req.write(dumps(fault, methodresponse=1))
        return apache.OK

    # Execute it.  The calling function is
    # responsive for responding to the request.
    Dispatch(req, method, args)

    return apache.OK
