# SPDX-License-Identifier: GPL-2.0-or-later
# File: apache-rteval.conf
#
# Apache config entry to enable the rteval XML-RPC server
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#
<Directory "{_INSTALLDIR_}">
    Options Indexes FollowSymLinks
    AllowOverride None
    Order allow,deny
    Allow from all

    SetHandler python-program
    PythonHandler rteval_xmlrpc
    PythonDebug On
</Directory>

