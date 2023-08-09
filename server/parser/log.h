/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2009 Red Hat Inc.
 *
 */

/**
 * @file   log.h
 * @author David Sommerseth <davids@redhat.com>
 * @date   Wed Oct 21 11:38:51 2009
 *
 * @brief  Generic log functions
 *
 */

#ifndef _RTEVAL_LOG_H
#define _RTEVAL_LOG_H

#include <pthread.h>
#include <syslog.h>

/**
 * Supported log types
 */
typedef enum { ltSYSLOG, ltFILE, ltCONSOLE } LogType;

/**
 * The log context structure.  Keeps needed information for
 * a flawless logging experience :-P
 */
typedef struct {
	LogType logtype;           /**<  What kind of log "device" will be used */
	FILE *logfp;               /**<  Only used if logging to stderr, stdout or a file */
	unsigned int verbosity;    /**<  Defines which log level the user wants to log */
	pthread_mutex_t *mtx_log;  /**<  Mutex to threads to write to a file based log in parallel */
} LogContext;


LogContext *init_log(const char *fname, const char *loglvl);
void close_log(LogContext *lctx);
void writelog(LogContext *lctx, unsigned int loglvl, const char *fmt, ... );

#endif
