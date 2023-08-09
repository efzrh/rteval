# SPDX-License-Identifier: GPL-2.0-or-later
# File: apache-rteval.conf
#
# Apache config entry to enable the rteval XML-RPC server
#
#   Copyright 2011 - 2013   David Sommerseth <davids@redhat.com>
#

WSGISocketPrefix /var/run/wsgi
WSGIDaemonProcess rtevalxmlrpc processes=3 threads=15 python-path={_INSTALLDIR_}
WSGIScriptAlias /rteval/API1 {_INSTALLDIR_}/rteval_xmlrpc.wsgi

<Directory "{_INSTALLDIR_}">
    Options Indexes FollowSymLinks
    AllowOverride None
    Order allow,deny
    Allow from all

    WSGIProcessGroup rtevalxmlrpc
    WSGICallableObject rtevalXMLRPC_handler
</Directory>

