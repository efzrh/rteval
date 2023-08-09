# SPDX-License-Identifier: GPL-2.0-or-later
#
#   rtevalclient.py
#   XML-RPC client for sending data to a central rteval result server
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import xmlrpc.client
import libxml2
import io
import bz2
import base64
import platform

class rtevalclient:
    """
    rtevalclient is a library for sending rteval reports to an rteval server via XML-RPC.
    """
    def __init__(self, url="http://rtserver.farm.hsv.redhat.com/rteval/API1/", hostn = None):
        self.srv = xmlrpc.client.ServerProxy(url)
        if hostn is None:
            self.hostname = platform.node()
        else:
            self.hostname = hostn

    def Hello(self):
        return self.srv.Hello(self.hostname)

    def DatabaseStatus(self):
        return self.srv.DatabaseStatus()

    def SendReport(self, xmldoc):
        if xmldoc.type != 'document_xml':
            raise Exception("Input is not XML document")

        fbuf = io.StringIO()
        xmlbuf = libxml2.createOutputBuffer(fbuf, 'UTF-8')
        doclen = xmldoc.saveFileTo(xmlbuf, 'UTF-8')

        compr = bz2.BZ2Compressor(9)
        cmpr = compr.compress(fbuf.getvalue())
        data = base64.b64encode(cmpr + compr.flush())
        ret = self.srv.SendReport(self.hostname, data)
        print(f"rtevalclient::SendReport() - Sent {len(data)} bytes (XML document length: {doclen} bytes, compression ratio: {(1-(float(len(data)) / float(doclen)))*100}:.2f)")
        return ret

    def SendDataAsFile(self, fname, data, decompr = False):
        compr = bz2.BZ2Compressor(9)
        cmprdata = compr.compress(data)
        b64data = base64.b64encode(cmprdata + compr.flush())
        return self.srv.StoreRawFile(self.hostname, fname, b64data, decompr)


    def SendFile(self, fname, decompr = False):
        f = open(fname, "r")
        srvname = self.SendDataAsFile(fname, f.read(), decompr)
        f.close()
        return srvname

