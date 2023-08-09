# SPDX-License-Identifier: GPL-2.0-or-later
#   Makefile.am - autotools configuration file
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#
SUBDIRS = parser
dist_doc_DATA = parser/README.parser 	\
	sql/delta-1.0_1.1.sql 		\
	sql/delta-1.1_1.2.sql 		\
	sql/delta-1.2_1.3.sql 		\
	sql/delta-1.3_1.4.sql 		\
	sql/rteval-$(SQLSCHEMAVER).sql

apache-rteval.conf:
if ENAB_MODPYTHON
	[ -n $(XMLRPCROOT) ] && $(srcdir)/gen_config.sh apache-rteval.conf $(XMLRPCROOT)/API1
else
	[ -n $(XMLRPCROOT) ] && $(srcdir)/gen_config.sh apache-rteval-wsgi.conf $(XMLRPCROOT)/API1
endif

clean-local:
	-rm -f apache-rteval.conf *~

dist-hook:
	cp $(srcdir)/gen_config.sh $(srcdir)/apache-rteval.conf.tpl $(srcdir)/apache-rteval-wsgi.conf.tpl $(distdir)/
	-rm -f $(distdir)/apache-rteval.conf

if ENAB_XMLRPC
    xmlrpcdir = $(XMLRPCROOT)/API1
    BUILT_SOURCES = apache-rteval.conf
    dist_doc_DATA += README.xmlrpc apache-rteval.conf
    dist_xmlrpc_DATA = xmlrpc_API1.py rtevaldb.py database.py
if ENAB_MODPYTHON
    dist_xmlrpc_DATA += rteval_xmlrpc.py
else
    dist_xmlrpc_DATA += rteval_xmlrpc.wsgi
endif
endif
