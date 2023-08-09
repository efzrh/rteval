# SPDX-License-Identifier: GPL-2.0-or-later
#   Makefile.am - autotools configuration file
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

# Generic include files, found by ./configure
AM_CPPFLAGS = $(LIBXML2_INC) $(LIBXSLT_INC) $(LIBPQ_INC) -std=gnu89

# What is required to build rteval_parserd
bin_PROGRAMS = rteval-parserd
rteval_parserd_SOURCES = argparser.c argparser.h 			 \
	configparser.c configparser.h 					 \
	eurephia_nullsafe.c eurephia_nullsafe.h eurephia_values_struct.h \
	eurephia_values.c eurephia_values.h 				 \
	eurephia_xml.c eurephia_xml.h 					 \
	log.c log.h  							 \
	parsethread.c parsethread.h threadinfo.h			 \
	pgsql.c pgsql.h 						 \
	sha1.c sha1.h							 \
	xmlparser.c xmlparser.h	             				 \
	rteval-parserd.c statuses.h

# Don't build, only install
xsltdir=$(datadir)/rteval
dist_xslt_DATA = xmlparser.xsl

# Copy init script and config file example to the docs dir
initscriptdir=$(docdir)/initscripts
dist_initscript_DATA = rteval-parserd.init rteval-parserd.sysconfig
