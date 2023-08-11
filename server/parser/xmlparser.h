/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2009 Red Hat Inc.
 *
 * David Sommerseth <davids@redhat.com>
 *
 *
 */

/**
 * @file   xmlparser.h
 * @author David Sommerseth <davids@redhat.com>
 * @date   Wed Oct 7 17:27:39 2009
 *
 * @brief Parses summary.xml reports from rteval into a standardised XML format
 *        which is useful when putting data into a database.
 *
 */


#ifndef _XMLPARSER_H
#define _XMLPARSER_H

/**
 *  Parameters needed by the the xmlparser.xsl XSLT template.
 */
typedef struct {
        const char *table;            /**< Which table to parse data for.  Required*/
        unsigned int submid;          /**< Submission ID, needed by the 'rtevalruns' table */
        unsigned int syskey;          /**< System key (referencing systems.syskey) */
        const char *report_filename;  /**< Filename to the saved report (after being parsed) */
        unsigned int rterid;          /**< References rtevalruns.rterid */
} parseParams;

/**
 * Container for string arrays
 */
typedef struct {
        unsigned int size;
        char **data;
} array_str_t;

array_str_t * strSplit(const char * str, const char * sep);
inline char * strGet(array_str_t * ar, unsigned int el);
inline unsigned int strSize(array_str_t * ar);
void strFree(array_str_t * ar);

/** Simple for-loop iterator for array_str_t objects
 *
 * @param ptr Return pointer (char *) where the element data is returned
 * @param idx Element index counter, declares where it should start and can be used
 *            to track the iteration process.  Must be an int variable
 * @param ar  The array_str_t object to iterate
 */
#define for_array_str(ptr, idx, ar) for( ptr = ar->data[idx]; idx++ < ar->size; \
                                         ptr=(idx < ar->size ? ar->data[idx] : NULL) )

/**
 *  Database specific helper functions
 */
typedef struct {
        char *(*dbh_FormatArray)(LogContext *log, xmlNode *sql_n); /** Formats data as arrays */
} dbhelper_func;

void init_xmlparser(dbhelper_func const * dbhelpers);
char * sqldataValueHash(LogContext *log, xmlNode *sql_n);
xmlDoc *parseToSQLdata(LogContext *log, xsltStylesheet *xslt, xmlDoc *indata_d, parseParams *params);
char *sqldataExtractContent(LogContext *log, xmlNode *sql_n);
int sqldataGetFid(LogContext *log, xmlNode *sqld, const char *fname);
char *sqldataGetValue(LogContext *log, xmlDoc *sqld, const char *fname, int recid);
xmlDoc *sqldataGetHostInfo(LogContext *log, xsltStylesheet *xslt, xmlDoc *summaryxml,
			   int syskey, char **hostname, char **ipaddr);
int sqldataGetRequiredSchemaVer(LogContext *log, xmlNode *sqldata_root);

#endif
