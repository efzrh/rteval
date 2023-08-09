/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Copyright (C) 2009 Red Hat Inc.
 *
 */

/**
 * @file   parsethread.h
 * @author David Sommerseth <davids@redhat.com>
 * @date   Thu Oct 15 11:52:10 2009
 *
 * @brief  Contains the "main" function which a parser threads runs
 *
 */

#ifndef _PARSETHREAD_H
#define _PARSETHREAD_H

/**
 * jbNONE means no job available,
 * jbAVAIL indicates that parseJob_t contains a job
*/
typedef enum { jbNONE, jbAVAIL } jobStatus;

/**
 * This struct is used for sending a parse job to a worker thread via POSIX MQ
 */
typedef struct {
        jobStatus status;                  /**< Info about if job information*/
        unsigned int submid;               /**< Work info: Numeric ID of the job being parsed */
        char clientid[256];                /**< Work info: Should contain senders hostname */
        char filename[4096];               /**< Work info: Full filename of the report to be parsed */
} parseJob_t;


void *parsethread(void *thrargs);

#endif
