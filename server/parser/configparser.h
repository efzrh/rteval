/* SPDX-License-Identifier: GPL-2.0-only */
/*  configparser.h - Read and parse config files
 *
 *  This code is based on the fragments from the eurephia project.
 *
 *  GPLv2 Copyright (C) 2009
 *  David Sommerseth <davids@redhat.com>
 *
 */

/**
 * @file   configparser.h
 * @author David Sommerseth <davids@redhat.com>
 * @date   2009-10-01
 *
 * @brief  Config file parser
 *
 */

#ifndef _CONFIGPARSER_H
#define _CONFIGPARSER_H

eurephiaVALUES *read_config(LogContext *log, eurephiaVALUES *prgargs, const char *section);

#endif
