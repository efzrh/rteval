# SPDX-License-Identifier: GPL-2.0-or-later
#
#   testclient.py
#   XML-RPC test client for testing the supported XML-RPC API 
#   in the rteval server.
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import sys
import libxml2
import io

sys.path.append('../rteval')
import rtevalclient

print("** Creating doc")
d = libxml2.newDoc("1.0")
n = libxml2.newNode('TestNode1')
d.setRootElement(n)
n2 = n.newTextChild(None, 'TestNode2','Just a little test')
n2.newProp('test','true')

for i in range(1,5):
    n2 = n.newTextChild(None, 'TestNode3', 'Test line %i' %i)

print("** Doc to be sent")
d.saveFormatFileEnc('-','UTF-8', 1)


print("** Testing API")
client = rtevalclient.rtevalclient("http://localhost:65432/rteval/API1/")

print("** 1: Hello(): %s" % str(client.Hello()))
status = client.SendReport(d)
print("** 2: SendReport(xmlDoc): %s" % str(status))

