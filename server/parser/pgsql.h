/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2009 Red Hat Inc.
 *
 */

/**
 * @file   pgsql.h
 * @author David Sommerseth <davids@redhat.com>
 * @date   Wed Oct 13 17:44:35 2009
 *
 * @brief  Database API for the PostgreSQL database.
 *
 *
 */

#ifndef _RTEVAL_PGSQL_H
#define _RTEVAL_PGSQL_H

#include <libpq-fe.h>
#include <libxml/parser.h>
#include <libxslt/transform.h>

#include <log.h>
#include <eurephia_values.h>
#include <parsethread.h>
#include <xmlparser.h>

/**
 *  A unified database abstraction layer, providing log support
 */
typedef struct {
	unsigned int id;           /**< Unique connection ID, used for debugging */
	LogContext *log;           /**< Initialised log context */
	PGconn *db;                /**< Database connection handler */
	unsigned int sqlschemaver; /**< SQL schema version, retrieved from rteval_info table */
	array_str_t *measurement_tbls; /**< Measurement tables to process */
} dbconn;

/* Generic database function */
dbconn *db_connect(eurephiaVALUES *cfg, unsigned int id, LogContext *log);
int db_ping(dbconn *dbc);
void db_disconnect(dbconn *dbc);
int db_begin(dbconn *dbc);
int db_commit(dbconn *dbc);
int db_rollback(dbconn *dbc);

/* rteval specific database functions */
int db_wait_notification(dbconn *dbc, const int *shutdown, const char *listenfor);
parseJob_t *db_get_submissionqueue_job(dbconn *dbc, pthread_mutex_t *mtx);
int db_update_submissionqueue(dbconn *dbc, unsigned int submid, int status);
int db_register_system(dbconn *dbc, xsltStylesheet *xslt, xmlDoc *summaryxml);
int db_get_new_rterid(dbconn *dbc);
int db_register_rtevalrun(dbconn *dbc, xsltStylesheet *xslt, xmlDoc *summaryxml,
			  unsigned int submid, int syskey, int rterid, const char *report_fname);
int db_register_measurements(dbconn *dbc, xsltStylesheet *xslt, xmlDoc *summaryxml, int rterid);

#endif
